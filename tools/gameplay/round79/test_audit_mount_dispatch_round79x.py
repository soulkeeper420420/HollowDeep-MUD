"""Round79X read-only dispatch audit boundary tests."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import audit_mount_dispatch_round79x as a

class TestRound79XAudit(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix=a.PREFIX+'test-',dir='/tmp')
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)/'src'
        self.root.mkdir()
        for name,content in {
            'frp.new':b'\x7fELF\x01test',
            'global.c':'{ "look", look, 0 },\n{ "north", move, 0 },\n',
            'wilderness.c':'int hd_wilderness_move(void);\nint hd79_wilderness_tile(int);\n',
            'mstruct.h':'typedef struct room room;\n',
            'mtype.h':'#define RMAX 10000\n',
        }.items():
            (self.root/name).write_bytes(content if isinstance(content,bytes) else content.encode())
    def test_readonly_native_command_collisions_absent(self):
        p=a.private(self.root)
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            a.audit(p)
        self.assertIn('Candidate command name collisions: NONE',out.getvalue())
    def test_existing_mount_command_denied(self):
        p=self.root/'global.c'
        p.write_text(p.read_text()+'{ "mount", existing, 0 },\n')
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,'duplicates'):
                a.audit(a.private(self.root))
    def test_elf64_denied(self):
        (self.root/'frp.new').write_bytes(b'\x7fELF\x02test')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            a.private(self.root)
    def test_live_denied(self):
        with self.assertRaisesRegex(ValueError,'disposable'):
            a.private('/srv/hollowdeep/world/src_3.00')
    def test_invalid_command_table_denied(self):
        (self.root/'global.c').write_text('not a command table\n')
        with self.assertRaisesRegex(ValueError,'grammar'):
            a.audit(a.private(self.root))
    def test_symlink_denied(self):
        p=self.root/'mstruct.h'
        p.unlink()
        p.symlink_to(self.root/'mtype.h')
        with self.assertRaisesRegex(ValueError,'unsafe'):
            a.private(self.root)
if __name__=='__main__':
    unittest.main(verbosity=2)
