"""R6C source-isolation, exact anchor and private lifecycle gate tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from stage_mount_ad_creature_action import (
    INCLUDE, MAKE_ANCHOR, patch_make, patch_identity, private)

class StageTests(unittest.TestCase):
    def setUp(self):
        self.make=('MOUNT_AD_AUTH_ACTION\nMOUNT_AD_ACTION_CAS\n'
                   +MAKE_ANCHOR+'frp.new: $(OBJECTS)\n')
        self.identity=('HD79_AD_COMBAT_DEATH_PLAYTEST\n'
                       '#include "hd79_ad_death_identity.inc"\n')
    def test_valid_gate(self):
        out=patch_make(self.make)
        self.assertIn('OBJECTS += hd79_ad_creature_action.o',out)
        self.assertLess(out.index('hd79_ad_creature_action.o'),out.index('frp.new:'))
    def test_exact_once(self):
        for source in (self.make+self.make,
                       self.make.replace(MAKE_ANCHOR,''),
                       self.make.replace('MOUNT_AD_ACTION_CAS',''),
                       self.make+'HD79_AD_SOCKET_TESTING'):
            with self.assertRaises(ValueError):patch_make(source)
    def test_duplicate_gate(self):
        with self.assertRaises(ValueError):patch_make(patch_make(self.make))
    def test_identity_requires_death(self):
        self.assertEqual(patch_identity(self.identity),self.identity+INCLUDE)
        for bad in ('garbage','HD79_AD_COMBAT_DEATH_PLAYTEST',
                    patch_identity(self.identity)):
            with self.assertRaises(ValueError):patch_identity(bad)
    def test_only_disposable_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for suffix in ('src','src/other'):
                with self.assertRaises(ValueError):private(root/suffix,
                          'hd-army-game-round79adcas-',False)
    def test_deny_root_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            link=root/'src';link.symlink_to(root)
            with self.assertRaises(ValueError):private(link,
                     'hd-army-game-round79adcas-',True)
    def test_source_documents_safe_boundaries(self):
        here=Path(__file__).resolve().parent
        source=(here/'hd79_ad_creature_action.c').read_text()
        self.assertIn('hd79_ad_authenticated_action_plan(',source)
        self.assertIn('hd79_ad_four_action_commit_native(',source)
        self.assertIn('hd79_ad_four_store_read(',source)
        self.assertIn('del_crt_rom(',source)
        self.assertIn('hd79_ad_private_spawn(',source)
        self.assertIn('return HD79_AD_CREATURE_PENDING;',source)
        identity=(here/'hd79_ad_bound_creature.inc').read_text()
        self.assertIn('native_same_room(',identity)
        self.assertIn('entry->epoch',identity)
        self.assertNotIn('strstr(',identity)
        self.assertNotIn('strcmp(entry->mount->name',identity)

if __name__=='__main__':unittest.main()
