"""Socket harness construction safety and exact-anchor tests."""
from pathlib import Path
import os
import stat
import tempfile
import unittest
from unittest.mock import patch
import build_stable_socket_round79z as b

SAMPLE='''import sys
from pathlib import Path
from breath_socket_reconnect import require_saved_login_banner
if SOURCE.parent.name.startswith("hd-army-game-round79rest-"):
    pass
HERE=Path(__file__).resolve().parent
prior["prepare_chroot"](exe,world)
        prior["login"](player,"Hdnecroqa")
        ask(player,"north","Necromancer Trial Annex")
        ask(returning,"skills","Breath 94/100")
'''
class SocketBuildTests(unittest.TestCase):
    def setUp(self):
        self.repo=tempfile.TemporaryDirectory(prefix='hd79z-repo-')
        self.output=tempfile.TemporaryDirectory(prefix='hd79z-output-')
        self.addCleanup(self.repo.cleanup);self.addCleanup(self.output.cleanup)
        self.root=Path(self.repo.name)
        self.src=self.root/'tools/gameplay/round79'
        self.src.mkdir(parents=True)
        self.file=self.src/'check_breath_rest_socket.py'
        self.file.write_text(SAMPLE)
        self.out=Path(self.output.name)/'stable_socket.py'
    def build(self):
        with patch.object(b.Path,'absolute',return_value=Path(
             '/root/hollowdeep-dev/round79z-test/stable_socket.py')):
            return b.build(self.root,self.out)
    def test_exact_stable_world_replay(self):
        result=self.build().read_text()
        self.assertIn('HDST1\\n2\\n10001\\n',result)
        self.assertIn('This room is a verified stable',result)
        self.assertIn('prior["prepare_chroot"](exe,world)',result)
        self.assertIn('os.chown(registry.parent,0,0)',result)
        self.assertIn('os.chown(registry,0,0)',result)
        self.assertIn('registry.parent.chmod(0o755)',result)
        self.assertIn('registry.chmod(0o644)',result)
        self.assertLess(result.index('prior["prepare_chroot"](exe,world)'),
                        result.index('os.chown(registry,0,0)'))
        self.assertIn('Refusing unsafe synthetic stable-registry fixture',result)
        self.assertIn('round79stable-',result)
        self.assertIn('No mounts registered',result)
    def test_root_owned_metadata_recovery_is_fixture_scoped(self):
        result=self.build().read_text()
        self.assertIn('world.parent != Path("/tmp")',result)
        self.assertIn('registry.parent != world/"hollowdeep-data"',result)
        self.assertIn('registry.is_symlink()',result)
        self.assertIn('registry.parent.is_symlink()',result)
        self.assertIn('registry.stat().st_uid != 0',result)

    @unittest.skipUnless(os.geteuid()==0, "root-only fixture ownership test")
    def test_restores_fixture_registry_after_chroot_normalization(self):
        result=self.build().read_text()
        assert 'prior["prepare_chroot"](exe,world)' in result
        script=result.split('prior["prepare_chroot"](exe,world)',1)[1]
        snippet=script.split('        prior["login"](player,"Hdnecroqa")',1)[0]
        # Simulate the known private helper's UID 65534 / mode changes
        # inside a fresh synthetic world, never in live source or players.
        with tempfile.TemporaryDirectory(
                prefix="hd79p-rest-socket-test-",dir="/tmp") as temp:
            world=Path(temp)
            registry=world/'hollowdeep-data'/'mount-stables.hds'
            registry.parent.mkdir()
            registry.write_text("HDST1\n2\n10001\n",encoding="ascii")
            os.chown(world,65534,65534)
            world.chmod(0o700)
            os.chown(registry.parent,65534,65534)
            registry.parent.chmod(0o700)
            os.chown(registry,65534,65534)
            registry.chmod(0o600)
            exec(snippet,{'world':world,'registry':registry,
                          'Path':Path,'os':os,'RuntimeError':RuntimeError})
            self.assertEqual(registry.stat().st_uid,0)
            self.assertEqual(registry.parent.stat().st_uid,0)
            self.assertEqual(stat.S_IMODE(registry.stat().st_mode),0o644)
            self.assertEqual(stat.S_IMODE(registry.parent.stat().st_mode),0o755)
            self.assertEqual(registry.read_text(),"HDST1\n2\n10001\n")
            self.assertEqual(world.stat().st_uid,65534)

    def test_altered_fixture_denied(self):
        self.file.write_text(SAMPLE.replace('Necromancer Trial Annex','different'))
        with self.assertRaisesRegex(ValueError,'anchor drift'):
            self.build()
        self.assertFalse(self.out.exists())
    def test_existing_target_denied(self):
        self.out.write_text('old')
        with self.assertRaisesRegex(ValueError,'new private'):
            self.build()
    def test_live_destination_denied(self):
        with self.assertRaisesRegex(ValueError,'new private'):
            b.build(self.root,'/srv/hollowdeep/world/unsafe.py')

if __name__=='__main__':unittest.main()
