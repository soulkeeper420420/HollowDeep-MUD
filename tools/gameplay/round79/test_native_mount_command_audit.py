"""Round79R: accepted private ELF32 mount/command flag audit safety tests."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import native_mount_command_audit as mount

class NativeMountAuditTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79rest-test-",dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.src=Path(temporary.name)/"src"
        self.src.mkdir()
        sources={
            "frp.new":b"\x7fELF\x01fixture",
            "global.c":(
                "struct cmd_record cmdlist[] = {\n"
                '  { "mount",100, action },\n'
                '  { "rest",100, hd79_rest_command },\n'
                "};\n"),
            "wilderness.c":"int hd79_wilderness_tile(int id) { return read_tile(id); }\n",
            "mstruct.h":"typedef struct creature { int mount; } creature;\n",
            "mtype.h":"#define PMOUNT 75 /* synthetic only */\n",
            "creature.c":"int mount_state(creature *p) {return 0;}\n"
        }
        for name,body in sources.items():
            (self.src/name).write_bytes(
                body if isinstance(body,bytes) else body.encode("latin-1"))

    def test_private_round79p_source_accepted(self):
        self.assertEqual(mount.source_dir(self.src),self.src)

    def test_mount_command_and_flags_reported(self):
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf):
            mount.audit(mount.source_dir(self.src))
        report=buf.getvalue()
        self.assertIn('  { "mount",100, action },',report)
        self.assertIn("PMOUNT 75",report)
        self.assertIn("ROUND 79G: MOUNT COMMAND/TERRAIN AUDIT COMPLETE",report)
        self.assertIn("NATIVE MOUNTS AND SAVE INTEGRATION: NOT YET ACTIVE",report)

    def test_prefixed_mount_symbols_detected_without_numeric_assumptions(self):
        # Atlas screenshots are NOT numeric/ABI specifications for
        # HollowDeep; these are synthetic spellings only.
        for name in ("PMOUNT","CMOUNT","OMOUNT","MMOUNT"):
            with self.subTest(name=name):
                self.assertTrue(mount.SYMBOL.search(
                    "#define "+name+" 999 /* synthetic fixture */"))
        self.assertFalse(mount.SYMBOL.search("#define PFLIGHT 75"))

    def test_absent_mount_flag_is_not_fabricated(self):
        (self.src/"mtype.h").write_text("#define PNOSUM 74\n")
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            mount.audit(mount.source_dir(self.src))
        data=output.getvalue()
        self.assertIn("mtype.h matches=0",data)
        self.assertNotIn("PMOUNT 75",data)
        self.assertIn("NATIVE MOUNTS AND SAVE INTEGRATION: NOT YET ACTIVE",data)

    def test_production_refused(self):
        with self.assertRaisesRegex(ValueError,"disposable"):
            mount.source_dir("/srv/hollowdeep/world/src_3.00")

    def test_elf64_refused(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02wrong")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            mount.source_dir(self.src)

    def test_symlink_native_file_refused(self):
        file=self.src/"global.c"
        file.unlink()
        file.symlink_to(self.src/"mtype.h")
        with self.assertRaisesRegex(ValueError,"exact private"):
            mount.source_dir(self.src)

    def test_missing_native_flag_header_refused(self):
        (self.src/"mtype.h").unlink()
        with self.assertRaisesRegex(ValueError,"exact private"):
            mount.source_dir(self.src)

if __name__=="__main__":
    unittest.main(verbosity=2)
