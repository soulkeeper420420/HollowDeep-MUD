#!/usr/bin/env python3
"""Round 78 workbench smoke and negative tests; no actual game service used."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from content import canonical, read, template, validate
from native import native_entry
from stage import staged_edits, private_path


class Round78Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='hd-round78-', dir='/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'source'
        self.source.mkdir()
        (self.source/'mtype.h').write_text('#define MAGE 5\n#define HUMAN 5\n')
        classes = ('Unknown','Assassin','Barbarian','Cleric','Fighter','Mage',
                   'Paladin','Ranger','Thief','Bard','Monk','Spare','Unused')
        races = ('Unknown','Dwarf','Elf','Half-elf','Hobbit','Human','Orc',
                 'Half-giant','Gnome','Troll','Half-orc','Ogre','Dark-elf','Goblin')
        def entries(values):
            return ', '.join(json.dumps(v) for v in values)
        stats = ',\n'.join('{1, 2, 3, 2, 5, 6, 7}' for _ in range(13))
        (self.source/'global.c').write_text(
            f'char class_str[][15] = {{{entries(classes)}}};\n'
            f'char race_str[][15] = {{{entries(races)}}};\n'
            f'class_stats[13] = {{\n{stats}\n}};\n')
        (self.source/'command1.c').write_text(
            'switch(Ply[fd].ply->race) {\n'
            '\t\tcase HUMAN:\n'
            '\t\t\tPly[fd].ply->constitution++;\n'
            '\t\t\tbreak;\n'
            '\t\t}\n')

    def draft(self, kind, key, edit):
        value, *_ = native_entry(self.source,kind,key)
        edit(value)
        draft=self.root/(kind+'-'+key+'.json')
        draft.write_text(canonical(value))
        return draft

    def test_class_native_stage_and_source_immutable(self):
        draft=self.draft('class','mage',lambda v: (
            v.update(name='Arcanist'),
            v['training'].update(hp_per_level=4,mp_per_level=3)))
        before={p.name:hashlib.sha256(p.read_bytes()).digest() for p in self.source.iterdir()}
        target=self.root/'staged'
        self.assertEqual(staged_edits(self.source,target,draft),['global.c'])
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).digest() for p in self.source.iterdir()})
        result, *_=native_entry(target,'class','mage')
        self.assertEqual(result['name'],'Arcanist')
        self.assertEqual(result['training'],{'hp_per_level':4,'mp_per_level':3})
        with self.assertRaisesRegex(ValueError,'Destination must be fresh'):
            staged_edits(self.source,target,draft)

    def test_race_native_stage_preserves_other_source(self):
        def edit(value):
            value['name']='Mannish'
            value['attributes']['dexterity']=2
        draft=self.draft('race','human',edit)
        target=self.root/'staged'
        self.assertEqual(staged_edits(self.source,target,draft),['command1.c','global.c'])
        result,*_=native_entry(target,'race','human')
        self.assertEqual(result['name'],'Mannish')
        self.assertEqual(result['attributes']['constitution'],1)
        self.assertEqual(result['attributes']['dexterity'],2)

    def test_new_class_requires_separate_native_integration(self):
        value=template('class','warlock','Warlock')
        value.update(description='Draft, not a playable class.')
        draft=self.root/'warlock.json'
        draft.write_text(canonical(value))
        with self.assertRaisesRegex(ValueError,'Unknown native class'):
            staged_edits(self.source,self.root/'stage',draft)
        self.assertFalse((self.root/'stage').exists())

    def test_unsupported_native_field_fails_closed(self):
        draft=self.draft('class','mage',lambda v:v.update(description='Changed'))
        with self.assertRaisesRegex(ValueError,'Native preview cannot apply'):
            staged_edits(self.source,self.root/'staged',draft)

    def test_duplicate_json_and_unsafe_attribute(self):
        draft=self.root/'invalid.json'
        draft.write_text('{"kind":"race","kind":"class"}')
        with self.assertRaisesRegex(ValueError,'Duplicate field'):
            read(draft)
        value=template('race','deep-dwarf','Deep Dwarf')
        value['attributes']['piety']=True
        with self.assertRaisesRegex(ValueError,'must be an integer'):
            validate(value)

    def test_symlinks_and_production_location_denied(self):
        self.assertRaises(ValueError,private_path,'/srv/hollowdeep/world', 'Source')
        draft=self.draft('class','mage',lambda v:v['training'].update(hp_per_level=5))
        (self.source/'unsafe-link').symlink_to(self.root/'outside')
        with self.assertRaisesRegex(ValueError,'Symlink in private'):
            staged_edits(self.source,self.root/'staged',draft)
        self.assertFalse((self.root/'staged').exists())

    def test_growth_and_label_limits_rejected(self):
        draft=self.draft('class','mage',lambda v:v['training'].update(hp_per_level=11))
        with self.assertRaisesRegex(ValueError,'between 1 and 10'):
            staged_edits(self.source,self.root/'staged',draft)
        draft=self.draft('race','human',lambda v:v['attributes'].update(dexterity=3))
        with self.assertRaisesRegex(ValueError,r'-2 to \+2'):
            staged_edits(self.source,self.root/'staged',draft)


if __name__=='__main__':
    unittest.main(verbosity=2)
