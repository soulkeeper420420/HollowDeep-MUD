"""No real source or production data: eight synthetic strict staging tests."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ad2stage',HERE/'stage_mount_ad_death_gate.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class StagingTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='hd79ad2-test-')
        self.addCleanup(temp.cleanup)
        # Actual stage() intentionally requires /tmp, mock workspace uses /tmp.
        self.original=Path(temp.name)/'Makefile'
        self.make=('MOUNT_AD_PRIVATE_FLEET=1\n'
                   'MOUNT_TRUSTED_SPAWN_PLAYTEST=1\n'
                   'OBJECTS += hd79_ad_private_transitions.o\nendif\n'
                   'frp.new: $(OBJECTS)\n\t@echo done\n')

    def test_good_gate_patches_exactly_once(self):
        result=mod.patch_make(self.make)
        self.assertIn('OBJECTS += hd79_ad_death_receipt.o',result)
        self.assertIn('OBJECTS += hd79_ad_verified_action.o',result)
        self.assertEqual(result.count('MOUNT_AD_DEATH_GATE'),2)

    def test_no_duplicate_accept(self):
        with self.assertRaisesRegex(ValueError,'drift'):
            mod.patch_make(self.make*2)

    def test_missing_anchor_denied(self):
        with self.assertRaises(ValueError):
            mod.patch_make(self.make.replace(mod.ANCHOR,''))

    def test_partial_or_existing_gate_denied(self):
        with self.assertRaises(ValueError):
            mod.patch_make(self.make+'MOUNT_AD_DEATH_GATE=1\n')

    def test_missing_original_private_gates_denied(self):
        with self.assertRaises(ValueError):
            mod.patch_make(self.make.replace('MOUNT_TRUSTED_SPAWN_PLAYTEST',''))

    def test_destination_is_private_and_fresh(self):
        with self.assertRaises(ValueError):
            mod.private('/srv/hollowdeep/world/src_3.00',mod.DEST_PREFIX,False)
        with self.assertRaises(ValueError):
            mod.private('/tmp/unrelated/src',mod.DEST_PREFIX,False)

    def test_source_path_cannot_be_production(self):
        with self.assertRaises(ValueError):
            mod.private('/srv/hollowdeep/world/src_3.00',mod.SOURCE_PREFIX,True)

    def test_private_source_never_opens_player_writes(self):
        stage=(HERE/'stage_mount_ad_death_gate.py').read_text()
        self.assertNotIn("PLAYERPATH",stage)
        runner=(HERE/'private_mount_ad_death_gate.sh').read_text()
        self.assertNotIn('systemctl restart',runner)
        self.assertNotIn('hd79_presence_store_commit(',
                         (HERE/'hd79_ad_verified_action.c').read_text())

if __name__=='__main__':unittest.main()
