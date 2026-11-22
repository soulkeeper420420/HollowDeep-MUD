"""Safety checks for Round79P -> Round79Y private socket harness."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_mount_socket_round79y as build

class SocketHarnessTests(unittest.TestCase):
    def setUp(self):
        self.repo=tempfile.TemporaryDirectory(prefix='hd79y-repo-')
        self.addCleanup(self.repo.cleanup)
        self.root=Path(self.repo.name)
        self.src=self.root/'tools/gameplay/round79'
        self.src.mkdir(parents=True)
        self.socket=self.src/'check_breath_rest_socket.py'
        self.socket.write_text('''import sys
from pathlib import Path
from breath_socket_reconnect import require_saved_login_banner
if SOURCE.parent.name.startswith("hd-army-game-round79rest-"):
    pass
HERE=Path(__file__).resolve().parent
        prior["login"](player,"Hdnecroqa")
        ask(returning,"skills","Breath 94/100")
''')

    def test_socket_harness_replaces_exact_anchors(self):
        # The helper allows only a private results destination.
        with tempfile.TemporaryDirectory(prefix='round79y-test-') as d:
            out=Path(d)/'check_mount_commands_socket.py'
            with patch.object(build.Path,'absolute',return_value=Path(
                 '/root/hollowdeep-dev/round79y-private/check_mount_commands_socket.py')):
                built=build.build(self.root,out)
            data=built.read_text()
            self.assertIn('hd-army-game-round79commands-',data)
            self.assertIn('PASS: real native mount commands',data)
            self.assertIn('ask(returning,"mount list"',data)
            self.assertIn(str(self.src),data)

    def test_socket_harness_rejects_anchor_drift(self):
        self.socket.write_text(self.socket.read_text().replace(
             'hd-army-game-round79rest-','unknown-native-source-'))
        with tempfile.TemporaryDirectory(prefix='round79y-test-') as d:
            out=Path(d)/'check_mount_commands_socket.py'
            with patch.object(build.Path,'absolute',return_value=Path(
                 '/root/hollowdeep-dev/round79y-private/check_mount_commands_socket.py')):
                with self.assertRaisesRegex(ValueError,'changed'):
                    build.build(self.root,out)
                self.assertFalse(out.exists())

    def test_live_target_denied(self):
        with self.assertRaisesRegex(ValueError,'target|private'):
            build.build(self.root,'/srv/hollowdeep/world/src_3.00/unsafe.py')

if __name__=='__main__':
    unittest.main()
