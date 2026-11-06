#!/usr/bin/env python3
"""Exercise smoke-client prompts and quit recovery without sockets or real sleeps."""
from collections import deque
import importlib.util
from pathlib import Path
import socket
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('runtime_smoke', Path(__file__).with_name('test_runtime.py'))
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration


class Connection:
    def __init__(self, clock, replies):
        self.clock = clock
        self.replies = deque(replies)
        self.incoming = deque()
        self.sent = []
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.sent.append(data)
        if self.replies:
            reply = self.replies.popleft()
            self.incoming.extend(reply if isinstance(reply, list) else [reply])

    def recv(self, size):
        if self.incoming:
            return self.incoming.popleft()
        self.clock.now += self.timeout
        raise socket.timeout()

    def close(self):
        self.closed = True


class QuitTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.process = Mock(returncode=None)
        self.process.poll.return_value = None
        monotonic = patch.object(runtime.time, 'monotonic', self.clock.monotonic)
        sleep = patch.object(runtime.time, 'sleep', self.clock.sleep)
        monotonic.start()
        sleep.start()
        self.addCleanup(monotonic.stop)
        self.addCleanup(sleep.stop)

    def client(self, replies, *, prompt_pattern=runtime.PROMPT):
        connection = Connection(self.clock, replies)
        return runtime.Client(connection, self.process, [], prompt_pattern=prompt_pattern), connection

    def test_immediate_goodbye(self):
        client, connection = self.client([b'Goodbye!\r\n'])
        client.quit()
        self.assertEqual(connection.sent, [b'quit\r\n'])
        self.assertTrue(connection.closed)
        self.assertEqual(self.clock.sleeps, [])

    def test_singular_cooldown_retries(self):
        client, connection = self.client([b'Please wait 1 more second.\n(10 H 10 M): ', b'Goodbye!'])
        client.quit()
        self.assertEqual(connection.sent, [b'quit\r\n'] * 2)
        self.assertEqual(self.clock.sleeps, [1.1])
        self.assertTrue(connection.closed)

    def test_new_character_twenty_second_cooldown(self):
        client, connection = self.client([b'Please wait 20 more seconds.\n(10 H 10 M): ', b'Goodbye!'])
        client.quit()
        self.assertEqual(self.clock.sleeps, [20.1])
        self.assertEqual(connection.sent, [b'quit\r\n'] * 2)

    def test_fragmented_cooldown_and_goodbye(self):
        client, connection = self.client([
            [b'Please wait 1', b' more second.', b'\r\n(10 H 10 M): '],
            [b'Good', b'bye!'],
        ])
        client.quit()
        self.assertEqual(self.clock.sleeps, [1.1])
        self.assertTrue(connection.closed)

    def test_repeated_cooldowns_share_one_deadline(self):
        client, connection = self.client([
            b'Please wait 20 more seconds.\n', b'Please wait 20 more seconds.\n',
            b'Please wait 5 more seconds.\n',
        ])
        with self.assertRaisesRegex(runtime.SmokeFailure, '45-second retry limit'):
            client.quit()
        self.assertEqual(connection.sent, [b'quit\r\n'] * 3)
        self.assertLess(self.clock.now, 45)
        self.assertFalse(connection.closed)

    def test_large_cooldown_is_rejected_without_sleep(self):
        client, connection = self.client([b'Please wait 999 more seconds.\n'])
        with self.assertRaisesRegex(runtime.SmokeFailure, '45-second retry limit'):
            client.quit()
        self.assertEqual(self.clock.sleeps, [])
        self.assertEqual(len(connection.sent), 1)

    def test_unrecognized_response_is_not_retried(self):
        client, connection = self.client([b'Please wait forever.\n(10 H 10 M): '])
        with self.assertRaisesRegex(runtime.SmokeFailure, 'timed out.*Please wait forever'):
            client.quit()
        self.assertEqual(connection.sent, [b'quit\r\n'])
        self.assertEqual(self.clock.sleeps, [])

    def test_disconnection_is_not_treated_as_success(self):
        client, connection = self.client([b''])
        with self.assertRaisesRegex(runtime.SmokeFailure, 'connection closed unexpectedly'):
            client.quit()
        self.assertEqual(len(connection.sent), 1)

    def test_engine_failure_is_not_retried(self):
        client, connection = self.client([])
        self.process.poll.return_value = 9
        self.process.returncode = 9
        with self.assertRaisesRegex(runtime.SmokeFailure, 'engine exited with 9'):
            client.quit()
        self.assertEqual(len(connection.sent), 1)

    def test_silent_server_times_out_without_retry(self):
        client, connection = self.client([])
        with self.assertRaisesRegex(runtime.SmokeFailure, 'timed out'):
            client.quit()
        self.assertEqual(len(connection.sent), 1)
        self.assertLess(self.clock.now, 13)

    def test_final_read_is_bounded_by_total_deadline(self):
        client, connection = self.client([b'Please wait 40 more seconds.\n'])
        with self.assertRaisesRegex(runtime.SmokeFailure, 'timed out'):
            client.quit()
        self.assertEqual(len(connection.sent), 2)
        self.assertLessEqual(self.clock.now, 45)

    def test_existing_string_and_prompt_reads_still_work(self):
        client, connection = self.client([b'Alpha\nBeta\n(10 H 10 M): after'])
        client.send('test')
        result = client.read_until(('Alpha', 'Beta'), prompt=True)
        self.assertEqual(result, 'Alpha\nBeta\n(10 H 10 M): ')
        self.assertEqual(client.pending, 'after')

    def test_founder_plain_prompt_can_arrive_in_fragments(self):
        client, connection = self.client([
            [b'Hollowdeep role: owner.\r', b'\n', b':', b' after'],
        ], prompt_pattern=runtime.PLAIN_PROMPT)
        result = client.command('hstaff whoami', 'role: owner')
        self.assertEqual(result, 'Hollowdeep role: owner.\n: ')
        self.assertEqual(client.pending, 'after')
        self.assertEqual(connection.sent, [b'hstaff whoami\r\n'])

    def test_embedded_staff_colon_is_not_a_founder_prompt(self):
        client, _ = self.client([
            b'STAFF ROSTER\nRealmkeeper: owner (configured founder)\n',
        ], prompt_pattern=runtime.PLAIN_PROMPT)
        with self.assertRaisesRegex(runtime.SmokeFailure, 'timed out'):
            client.command('hstaff list', 'STAFF ROSTER')

    def test_ordinary_player_still_requires_hp_mp_prompt(self):
        client, _ = self.client([b'Player saved.\n: '])
        with self.assertRaisesRegex(runtime.SmokeFailure, 'timed out'):
            client.command('save', 'Player saved.')


class SaveCompletionTests(unittest.TestCase):
    def test_new_login_greeting_is_required_before_restart(self):
        checkpoint = Mock()
        with patch.object(runtime, 'connect', return_value=checkpoint) as connect:
            runtime.wait_for_completed_quit(4040, 'process', ['test-secret'])
        connect.assert_called_once_with(4040, 'process', ['test-secret'])
        checkpoint.read_until.assert_called_once_with('Please enter name: ', label='quit save completion')
        checkpoint.close.assert_called_once_with()

    def test_failed_completion_check_is_closed_and_propagated(self):
        checkpoint = Mock()
        checkpoint.read_until.side_effect = runtime.SmokeFailure('engine stopped')
        with patch.object(runtime, 'connect', return_value=checkpoint):
            with self.assertRaisesRegex(runtime.SmokeFailure, 'engine stopped'):
                runtime.wait_for_completed_quit(4040, 'process', [])
        checkpoint.close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
