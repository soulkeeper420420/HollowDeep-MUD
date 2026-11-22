"""Round79X private native staging fail-closed unit tests."""
from pathlib import Path
import hashlib
import tempfile
import unittest
import stage_mount_actions_round79x as s

class TestRound79XStage(unittest.TestCase):
    def setUp(self):
        a=tempfile.TemporaryDirectory(prefix=s.SOURCE_PREFIX+'test-',dir='/tmp')
        b=tempfile.TemporaryDirectory(prefix=s.TARGET_PREFIX+'test-',dir='/tmp')
        self.addCleanup(a.cleanup)
        self.addCleanup(b.cleanup)
        self.source=Path(a.name)/'src'
        self.target=Path(b.name)/'src'
        self.source.mkdir()
        for name in s.REQUIRED:
            if name=='Makefile':
                content=s.GATE
            elif name=='frp.new':
                content=b'\x7fELF\x01test'
            else:
                content='/* private native fixture */\n'
            (self.source/name).write_bytes(
                content if isinstance(content,bytes) else content.encode('latin-1'))
    def test_valid_private_copy_without_gameplay_edits(self):
        old={(p.name,hashlib.sha256(p.read_bytes()).hexdigest())
             for p in self.source.iterdir()}
        s.stage(self.source,self.target)
        self.assertEqual(old, {(p.name,hashlib.sha256(p.read_bytes()).hexdigest())
                               for p in self.source.iterdir()})
        self.assertIn('MOUNT_ACTION_PLAYTEST',(self.target/'Makefile').read_text())
        self.assertEqual((self.target/'global.c').read_bytes(),
                         (self.source/'global.c').read_bytes())
        self.assertEqual((self.target/'wilderness.c').read_bytes(),
                         (self.source/'wilderness.c').read_bytes())
        for name in s.ADDED:
            self.assertTrue((self.target/name).is_file())
    def test_production_denied(self):
        with self.assertRaisesRegex(ValueError,'disposable'):
            s.stage(Path('/srv/hollowdeep/world/src_3.00'),self.target)
    def test_destination_must_be_new(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError,'already exists'):
            s.stage(self.source,self.target)
    def test_elf64_denied(self):
        (self.source/'frp.new').write_bytes(b'\x7fELF\x02test')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            s.stage(self.source,self.target)
    def test_missing_make_anchor_denied(self):
        (self.source/'Makefile').write_text('NO BUILD GATE\n')
        with self.assertRaisesRegex(ValueError,'gate drift'):
            s.stage(self.source,self.target)
    def test_already_staged_denied(self):
        (self.source/'Makefile').write_text(s.GATE+s.EXTENSION)
        with self.assertRaisesRegex(ValueError,'already installed'):
            s.stage(self.source,self.target)
    def test_source_symlink_denied(self):
        (self.source/'unsafe').symlink_to(self.source/'global.c')
        with self.assertRaisesRegex(ValueError,'symlink'):
            s.stage(self.source,self.target)
    def test_native_file_symlink_denied(self):
        p=self.source/'global.c'
        p.unlink()
        p.symlink_to(self.source/'wilderness.c')
        with self.assertRaisesRegex(ValueError,'unsafe'):
            s.stage(self.source,self.target)
    def test_no_autowrite_to_production(self):
        text=(Path(__file__).parent/'stage_mount_actions_round79x.py').read_text()
        self.assertNotIn('systemctl restart',text)
        self.assertNotIn('subprocess.',text)
        self.assertNotIn('PLAYERPATH',text)
    def test_missing_required_file_denied(self):
        (self.source/'hd79_mount_store.h').unlink()
        with self.assertRaisesRegex(ValueError,'missing'):
            s.stage(self.source,self.target)

if __name__=='__main__':
    unittest.main(verbosity=2)
