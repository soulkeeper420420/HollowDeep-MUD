"""Round79T: private native receipt audit source-safety regression tests."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import audit_native_mount_receipt_capacity as audit

class NativeMountReceiptAuditTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79rest-audit-",dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.src=Path(temporary.name)/"src"
        self.src.mkdir()
        data={
            "frp.new":b"\x7fELF\x01fake",
            "hd_player_store.c":(
                "typedef hd_receipt_set my_receipts;\n"
                'static const char breath_id[] = "ffffffffffffffffffffffffffffff79";\n'
                "int write_player(void) {\n"
                "  hd_receipt_set receipts;\n"
                "  hd_atomic_player_snapshot(PLAYERPATH,0,0,0);\n"
                "  return 0;\n"
                "}\n"
                '#include "hd_breath_store.inc"\n'),
            "treasure_receipt.h":(
                "#define HD_RECEIPT_MAX_ENTRIES 64\n"
                "int hd_receipt_add(void);\n"
                "int hd_receipt_encode(void);\n"),
            "treasure_receipt.c":(
                "int hd_receipt_add(void) {return 0;}\n"
                "int hd_receipt_encode(void) {return 0;}\n"),
            "hd_breath_store.inc":"int hd_breath_store_transaction(void);\n",
            "hd_conjure_store.inc":"/* preserved */\n"
        }
        for name,body in data.items():
            (self.src/name).write_bytes(
                body if isinstance(body,bytes) else body.encode("latin-1"))

    def test_private_elf32_contract_found(self):
        root,files=audit.validate(self.src)
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            audit.inspect(root,files)
        result=out.getvalue()
        self.assertIn("HD_RECEIPT_MAX_ENTRIES 64",result)
        self.assertIn("NATIVE RECEIPT CONTRACT SYMBOLS: FOUND",result)
        self.assertIn("Two mount receipt IDs reserved: NO",result)
        self.assertIn("ROUND79T: PRIVATE NATIVE RECEIPT CAPACITY AUDIT PASS",result)

    def test_production_denied(self):
        with self.assertRaisesRegex(ValueError,"disposable"):
            audit.validate("/srv/hollowdeep/world/src_3.00")

    def test_elf64_denied(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02fake")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            audit.validate(self.src)

    def test_symlinked_receipt_source_denied(self):
        file=self.src/"treasure_receipt.c"
        file.unlink()
        file.symlink_to(self.src/"treasure_receipt.h")
        with self.assertRaisesRegex(ValueError,"private receipt source"):
            audit.validate(self.src)

    def test_missing_breath_include_refused(self):
        file=self.src/"hd_player_store.c"
        file.write_text(file.read_text().replace(
            '#include "hd_breath_store.inc"',"/* disabled */"))
        root,files=audit.validate(self.src)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"contract not found"):
                audit.inspect(root,files)

    def test_missing_snapshot_contract_refused(self):
        file=self.src/"hd_player_store.c"
        file.write_text(file.read_text().replace(
            "hd_atomic_player_snapshot","not_a_real_snapshot"))
        root,files=audit.validate(self.src)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"contract not found"):
                audit.inspect(root,files)

    def test_no_native_file_mutation(self):
        code=(Path(__file__).parent/"audit_native_mount_receipt_capacity.py"
              ).read_text()
        self.assertNotIn("write_text(",code)
        self.assertNotIn("write_bytes(",code)
        self.assertNotIn("shutil.",code)
        self.assertNotIn("subprocess.",code)

if __name__=="__main__":
    unittest.main(verbosity=2)
