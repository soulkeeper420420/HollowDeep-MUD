"""Synthetic Round79AC3D fixed-record read-only scanner tests."""
import struct
import tempfile
import unittest
from pathlib import Path
import native_template_inventory_round79ac3d as scan

OFFSETS=(300,301,302,304)
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
        self.assertIn("NO CATALOG CONFIGURED",scan.report(self.mon,files,living,results))

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
            scan.parse_abi("HD79_NATIVE_ABI 1000 0 300 301 302 304 1")

    def test_abi_exact_offsets(self):
        self.assertEqual(
            scan.parse_abi("HD79_NATIVE_ABI 1184 0 300 301 302 304 1"),
            OFFSETS)

    def test_skip_private_player_subtrees(self):
        (self.mon/"m00").write_bytes(b"")
        priv=self.root/"players"
        priv.mkdir()
        (priv/"m00").write_bytes(b"")
        self.assertEqual(scan.discover(self.root),self.mon)
if __name__=="__main__":
    unittest.main()
