"""Synthetic Round79AC3D fixed-record read-only scanner tests."""
import struct
import tempfile
import unittest
from pathlib import Path
import native_template_inventory_round79ac3d as scan

# Synthetic offsets plus the *actual compiled* HollowDeep CMAX of 1000.
OFFSETS=(300,301,302,304,1000)
class TemplateInventoryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="hd79-ac3d-fixture-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.mon=self.root/"mon"
        self.mon.mkdir()

    def record(self,name,kind=1,hp=40,level=10):
        b=bytearray(scan.RECORD)
        b[:len(name)]=name.encode("ascii")
        b[OFFSETS[0]]=kind
        b[OFFSETS[1]]=level
        struct.pack_into("<h",b,OFFSETS[2],hp)
        struct.pack_into("<h",b,OFFSETS[3],hp)
        return bytes(b)

    def test_native_candidates_never_authorized(self):
        (self.mon/"m00").write_bytes(
            self.record("horse")+self.record("griffin")+self.record("orc"))
        self.assertEqual(scan.discover(self.root),self.mon)
        files,living,results=scan.inspect(self.mon,OFFSETS)
        self.assertEqual((files,living,len(results)),(1,3,2))
        self.assertEqual([row[0] for row in results],[0,1])
        self.assertIn("NO CATALOG CONFIGURED",scan.report(self.mon,files,living,results,OFFSETS[4]))

    def test_no_root_match_denied(self):
        with self.assertRaisesRegex(ValueError,"exactly one"):
            scan.discover(self.root)

    def test_ambiguous_dirs_denied(self):
        (self.mon/"m00").write_bytes(b"")
        extra=self.root/"other"
        extra.mkdir()
        (extra/"m00").write_bytes(b"")
        with self.assertRaisesRegex(ValueError,"exactly one"):
            scan.discover(self.root)

    def test_no_symlink_files(self):
        (self.mon/"m00").symlink_to(self.root/"bad")
        with self.assertRaisesRegex(ValueError,"Symlink"):
            scan.discover(self.root)

    def test_bad_binary_length_denied(self):
        (self.mon/"m00").write_bytes(b"invalid")
        with self.assertRaisesRegex(ValueError,"record size"):
            scan.inspect(self.mon,OFFSETS)

    def test_invalid_or_dead_creature_ignored(self):
        (self.mon/"m00").write_bytes(
            self.record("dragon",kind=0)+self.record("horse",hp=0))
        files,living,matches=scan.inspect(self.mon,OFFSETS)
        self.assertEqual((files,living,len(matches)),(1,0,0))

    def test_real_abi_size_mandatory(self):
        with self.assertRaises(ValueError):
            scan.parse_abi("unverified")
        with self.assertRaises(ValueError):
            scan.parse_abi("HD79_NATIVE_ABI 1000 0 300 301 302 304 1 100 3000")
        with self.assertRaises(ValueError):
            scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1")

    def test_abi_exact_offsets(self):
        self.assertEqual(
            scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1 100 1000"),
            OFFSETS)

    def test_reject_changed_native_index_limits(self):
        with self.assertRaisesRegex(ValueError,"indexing ABI"):
            scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1 99 3000")
        with self.assertRaisesRegex(ValueError,"indexing ABI"):
            scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1 100 2999")

    def test_compiled_3000_limit_is_supported_but_not_assumed(self):
        other=scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1 100 3000")
        self.assertEqual(other,OFFSETS[:4]+(3000,))

    def test_scans_only_compiled_template_id_range(self):
        (self.mon/"m00").write_bytes(self.record("a horse"))
        (self.mon/"m09").write_bytes(self.record("a dragon"))
        # Inaccessible beyond CMAX=1000; this must never be opened.
        (self.mon/"m10").write_bytes(b"malformed")
        files,living,results=scan.inspect(self.mon,OFFSETS)
        self.assertEqual((files,living), (2,2))
        self.assertEqual([entry[0] for entry in results], [0,900])
        self.assertIn("Native loadable slots (compiled CMAX): 1000",
                      scan.report(self.mon,files,living,results,OFFSETS[4]))
        with self.assertRaisesRegex(ValueError,"record size"):
            scan.inspect(self.mon,OFFSETS[:4]+(3000,))

    def test_missing_or_untrusted_template_limit_denied(self):
        (self.mon/"m00").write_bytes(self.record("horse"))
        with self.assertRaisesRegex(ValueError,"authoritative native CMAX"):
            scan.inspect(self.mon,OFFSETS[:4])
        with self.assertRaisesRegex(ValueError,"native CMAX"):
            scan.inspect(self.mon,OFFSETS[:4]+(2999,))
        for limit in (0,99,3100,999):
            with self.assertRaisesRegex(ValueError,"indexing ABI"):
                scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1 100 "+str(limit))

    def test_runner_does_not_require_nonexistent_source(self):
        here=Path(__file__).resolve().parent
        script=(here/"private_native_template_inventory_round79ac3d.sh").read_text()
        self.assertNotIn('$SOURCE/files4.c',script)
        probe=(here/"native_template_abi_round79ac3d.c").read_text()
        self.assertIn("MFILESIZE,CMAX",probe)
        self.assertIn("MONSTER,MFILESIZE,CMAX",probe)

    def test_skip_private_player_subtrees(self):
        (self.mon/"m00").write_bytes(b"")
        priv=self.root/"players"
        priv.mkdir()
        (priv/"m00").write_bytes(b"")
        self.assertEqual(scan.discover(self.root),self.mon)
if __name__=="__main__":
    unittest.main()
