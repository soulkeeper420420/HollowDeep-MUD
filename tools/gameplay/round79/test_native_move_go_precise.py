"""Round 79J: ensure compact private native move/go extractor is accurate."""
from pathlib import Path
import contextlib
import io
import tempfile
import unittest

import native_move_go_precise as native

FUNCTIONS="""int move(ply_ptr, cmnd)
creature *ply_ptr;
cmd *cmnd;
{
    /* a comment with } must not terminate the function */
    print("room } is a string");
    if (ply_ptr->rom_num == 2) {
        ply_ptr->rom_num = 10001;
    }
    return(0);
}
int go(ply_ptr, cmnd)
creature *ply_ptr;
cmd *cmnd;
{
    if (ply_ptr->rom_num > 0)
        return move(ply_ptr,cmnd);
    return(0);
}
"""

class PreciseMoveSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79store-source-",dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.src=Path(self.temp.name)/"src"
        self.src.mkdir()
        (self.src/"frp.new").write_bytes(b"\x7fELF\x01fixture")
        (self.src/"command6.c").write_text(FUNCTIONS,encoding="latin-1")

    def test_extract_k_and_r_both_functions(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            native.extract(native.check(self.src))
        data=output.getvalue()
        self.assertIn("NATIVE move() verified definitions: 1",data)
        self.assertIn("NATIVE go() verified definitions: 1",data)
        self.assertIn("room } is a string",data)
        self.assertIn("ply_ptr->rom_num = 10001",data)
        self.assertIn("EXACT NATIVE GO/MOVE FUNCTION SOURCE PASS",data)

    def test_prototype_not_a_function(self):
        lines=["int move(creature *x);","void foo() {}"]
        self.assertIsNone(native.end_function(lines,0))

    def test_production_denied(self):
        with self.assertRaisesRegex(ValueError,"verified private"):
            native.check(Path("/srv/hollowdeep/world/src_3.00"))

    def test_symlink_denied(self):
        (self.src/"unsafe.c").symlink_to(self.src/"command6.c")
        with self.assertRaisesRegex(ValueError,"symlink"):
            native.check(self.src)

    def test_wrong_architecture_denied(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02x64")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            native.check(self.src)

    def test_missing_actual_go_denied(self):
        (self.src/"command6.c").write_text(FUNCTIONS.split("int go")[0])
        with self.assertRaisesRegex(ValueError,"exactly one"):
            native.extract(native.check(self.src))

if __name__=="__main__":
    unittest.main(verbosity=2)
