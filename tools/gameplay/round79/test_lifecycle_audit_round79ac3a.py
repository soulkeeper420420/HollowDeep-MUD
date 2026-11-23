"""Round79AC3A strict private room/creature lifecycle auditor tests."""
import tempfile
import unittest
from pathlib import Path
import lifecycle_audit_round79ac3a as audit

class Audit(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(
            prefix=audit.ROOT_PREFIX+"audit-",dir="/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"src"
        self.root.mkdir()
        for name in audit.MANDATORY:
            (self.root/name).write_bytes(b"/* private */\n")
        (self.root/"frp.new").write_bytes(b"\x7fELF\x01mock")
        (self.root/"room.c").write_text("""
        void add_crt_rom(void *x) { /* free_crt(x); */ }
        void del_crt_rom(void *x) { free_crt(x); }
        // hd79_world_mount_bind(x);
        void unload(void) { free_rom(0); }
        """)
        (self.root/"creature.c").write_text(
            'void kill(void) { del_crt_rom(0); free_crt(0); }\n')
        (self.root/"command5.c").write_text(
            'int quit(void) { del_ply_rom(0); return 0; }\n')

    def test_inventory(self):
        m= audit.private_source(self.root)
        calls,active=audit.inspect(m)
        self.assertEqual(active,[])
        self.assertEqual(len(calls["add_crt_rom"]),1)
        self.assertEqual(len(calls["free_crt"]),2)
        self.assertEqual(len(calls["hd79_world_mount_bind"]),0)
        report=audit.format_report(calls,active)
        self.assertIn("ROOM/CREATURE/LOGOUT CALLSITE INVENTORY COMPLETE",report)

    def test_strings_comments_do_not_count(self):
        (self.root/"creature.c").write_text(
            'char *s="hd79_world_mount_bind(x)";'
            ' /* hd79_world_mount_bind(z) */\n'
            'void x(void){ /* free_crt(x); */ }\n')
        calls,active=audit.inspect(self.root)
        self.assertEqual(active,[])
        self.assertEqual(len(calls["hd79_world_mount_bind"]),0)

    def test_unexpected_game_hook_denied(self):
        (self.root/"command5.c").write_text(
            'void x(void){ hd79_world_mount_bind(0); }\n')
        calls,active=audit.inspect(self.root)
        self.assertEqual(active,[("hd79_world_mount_bind","command5.c",1)])

    def test_private_only(self):
        with self.assertRaisesRegex(ValueError,"Only accepted disposable"):
            audit.private_source(Path("/srv/hollowdeep/world/src_3.00"))

    def test_bad_elf_denied(self):
        (self.root/"frp.new").write_bytes(b"false")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            audit.private_source(self.root)

    def test_symlink_denied(self):
        (self.root/"redirect").symlink_to(self.root/"room.c")
        with self.assertRaisesRegex(ValueError,"Symlink"):
            audit.private_source(self.root)

    def test_missing_native_room_definition_denied(self):
        (self.root/"room.c").write_text("/* original definitions removed */")
        with self.assertRaisesRegex(ValueError,"definitions changed"):
            audit.inspect(self.root)

    def test_missing_native_file_denied(self):
        (self.root/"creature.c").unlink()
        with self.assertRaisesRegex(ValueError,"Missing or symlink"):
            audit.private_source(self.root)

if __name__=="__main__":
    unittest.main()
