#!/usr/bin/env python3
"""Round 78B deterministic schema and rebirth-unlock tests."""
import json
from pathlib import Path
import tempfile
import unittest
from content import template, canonical
from progression import template as progression_template, validate, load, unlocked


class ProgressionTests(unittest.TestCase):
    def setUp(self):
        self.defn = template('class', 'warlock', 'Warlock')
        self.defn['abilities'] = ['hex', 'blood-pact']
        self.defn['description'] = 'Test class draft'
        self.plan = progression_template(self.defn, ('intelligence', 'piety'))
        self.plan['skill_unlocks'] = [
            {'skill': 'hex', 'level': 1, 'rebirth': 0},
            {'skill': 'blood-pact', 'level': 1, 'rebirth': 1},
        ]

    def test_initial_and_reborn_unlocks(self):
        validate(self.defn, self.plan)
        self.assertEqual(unlocked(self.plan, 1, 0), ['hex'])
        self.assertEqual(unlocked(self.plan, 1, 1), ['hex', 'blood-pact'])
        self.assertEqual(unlocked(self.plan, 60, 1), ['hex', 'blood-pact'])

    def test_reject_bool_and_unbounded_values(self):
        for field in ('points', 'minimum', 'maximum'):
            data=json.loads(canonical(self.plan))
            data['starting_stats'][field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(self.defn, data)
        data=json.loads(canonical(self.plan))
        data['skill_unlocks'][0]['rebirth'] = -1
        with self.assertRaises(ValueError):
            validate(self.defn, data)
        data['skill_unlocks'][0]['level'] = 61
        with self.assertRaises(ValueError):
            validate(self.defn, data)

    def test_duplicate_primes_and_skills(self):
        data=json.loads(canonical(self.plan))
        data['prime_attributes']=['piety', 'piety']
        with self.assertRaisesRegex(ValueError,'prime_attributes'):
            validate(self.defn, data)
        data=json.loads(canonical(self.plan))
        data['skill_unlocks'].append({'skill':'hex','level':60,'rebirth':1})
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            validate(self.defn, data)

    def test_unknown_abilities_and_wrong_class(self):
        data=json.loads(canonical(self.plan))
        data['skill_unlocks'][0]['skill']='delete-saves'
        with self.assertRaisesRegex(ValueError,'reference an ability'):
            validate(self.defn, data)
        data=json.loads(canonical(self.plan))
        data['class_key']='vampire'
        with self.assertRaisesRegex(ValueError,'does not match'):
            validate(self.defn, data)

    def test_random_base_stats(self):
        data=json.loads(canonical(self.plan))
        data['starting_stats']={'mode':'random','ranges':{
            attr:{'min':8,'max':18} for attr in (
                'strength','dexterity','constitution','intelligence','piety')}}
        validate(self.defn, data)
        data['starting_stats']['ranges']['intelligence']['min']=19
        with self.assertRaises(ValueError):
            validate(self.defn, data)
        data['starting_stats']['ranges']['intelligence']={'min':17,'max':13}
        with self.assertRaisesRegex(ValueError,'minimum exceeds'):
            validate(self.defn, data)

    def test_selectable_requires_complete_unlock_mapping(self):
        self.defn['selectable']=True
        validate(self.defn, self.plan)
        self.plan['skill_unlocks'].pop()
        with self.assertRaisesRegex(ValueError,'every ability'):
            validate(self.defn,self.plan)

    def test_extra_and_duplicate_json_rejected(self):
        self.plan['unsafe_path']='../../live'
        with self.assertRaisesRegex(ValueError,'exactly'):
            validate(self.defn,self.plan)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'plan.json'
            p.write_text('{"kind":"class-progression","kind":"duplicate"}')
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                load(p,self.defn)


if __name__=='__main__':
    unittest.main(verbosity=2)
