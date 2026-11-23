"""Round79AC3E native monster template risk review synthetic tests."""
import struct
import tempfile
import unittest
from pathlib import Path
import native_mount_candidate_review_round79ac3e as risk
import native_template_inventory_round79ac3d as inv

ABI=(300,301,302,304,1000)
TRAITS="HD79_AC3E 1184 310 312 314 316 318 400 16 420 16 440 20"
class NativeRiskTest(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="hd79ac3e-mock-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.db=self.root/"monster"
        self.db.mkdir()
        self.fields=risk.decode_traits(TRAITS)

    def record(self,name,spell=False):
        row=bytearray(inv.RECORD)
        row[:len(name)]=name.encode("ascii")
        row[ABI[0]]=1
        row[ABI[1]]=8
        struct.pack_into("<h",row,ABI[2],50)
        struct.pack_into("<h",row,ABI[3],50)
        struct.pack_into("<h",row,310,20)
        struct.pack_into("<h",row,312,20)
        if spell:row[420]=3
        return bytes(row)

    def test_metadata_from_native_probe(self):
        self.assertEqual(self.fields["carry_len"],20)
        with self.assertRaises(ValueError):
            risk.decode_traits("HD79_AC3E 1184 0")
        with self.assertRaises(ValueError):
            risk.decode_traits(TRAITS.replace(" 400 16"," 310 16"))

    def test_readonly_review_never_approves(self):
        (self.db/"m00").write_bytes(self.record("traveling horse"))
        record=risk.native_record(self.db,0,1000)
        item=(0,"horse","traveling horse",8,50,50)
        status=risk.review_entry(item,record,ABI,self.fields)
        self.assertEqual(status[-2],"MANUAL_REVIEW")
        self.assertIn("NO TEMPLATE APPROVED",risk.report([status]))

    def test_magic_and_nonmount_denied_approval(self):
        for name in ("griffon statue","the Fenris Wolf","dragon puppet"):
            item=(0,"dragon",name,8,50,50)
            self.assertEqual(risk.review_entry(item,self.record(name),ABI,self.fields)[-2],
                             "EXCLUDE_NAME")
        item=(0,"griffin","griffon",8,50,50)
        self.assertEqual(risk.review_entry(item,self.record("griffon",True),ABI,self.fields)[-2],
                         "MANUAL_MAGIC_REVIEW")

    def test_changed_candidate_rejected(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            risk.review_entry((0,"horse","horse",8,50,50),
                              self.record("another monster"),ABI,self.fields)

    def test_native_cmax_enforced(self):
        (self.db/"m00").write_bytes(self.record("horse"))
        with self.assertRaisesRegex(ValueError,"CMAX"):
            risk.native_record(self.db,1000,1000)

    def test_native_symlink_denied(self):
        (self.root/"original").write_bytes(self.record("horse"))
        (self.db/"m00").symlink_to(self.root/"original")
        with self.assertRaises(OSError):
            risk.native_record(self.db,0,1000)

if __name__=="__main__":
    unittest.main()
