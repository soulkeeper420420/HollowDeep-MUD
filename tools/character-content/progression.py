#!/usr/bin/env python3
"""Validate class progression plans without changing the native MUD or its saves."""
import argparse
import json
from pathlib import Path
import sys

from content import ATTRIBUTES, SLUG, canonical, read, unique_pairs


KEYS = ('schema_version', 'kind', 'class_key', 'prime_attributes',
        'starting_stats', 'skill_unlocks')
STAT_KEYS = ('mode', 'points', 'minimum', 'maximum')
RANDOM_KEYS = ('mode', 'ranges')
UNLOCK_KEYS = ('skill', 'level', 'rebirth')


def plain_int(value, minimum, maximum, label):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{label} must be an integer between {minimum} and {maximum}')


def exact(value, keys, label):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(f'{label} must contain exactly {", ".join(keys)}')


def template(definition, primes):
    if definition['kind'] != 'class':
        raise ValueError('Progression applies only to classes')
    return {'schema_version': 1, 'kind': 'class-progression',
            'class_key': definition['key'], 'prime_attributes': list(primes),
            'starting_stats': {'mode': 'allocated', 'points': 65,
                               'minimum': 3, 'maximum': 18},
            'skill_unlocks': []}


def validate(definition, spec):
    if definition['kind'] != 'class':
        raise ValueError('Progression requires a class definition')
    exact(spec, KEYS, 'progression')
    if type(spec['schema_version']) is not int or spec['schema_version'] != 1:
        raise ValueError('Unsupported progression schema_version')
    if spec['kind'] != 'class-progression' or spec['class_key'] != definition['key']:
        raise ValueError('Progression class_key does not match the class definition')
    primes = spec['prime_attributes']
    if (type(primes) is not list or len(primes) != 2 or
            any(type(name) is not str or name not in ATTRIBUTES for name in primes) or
            len(set(primes)) != 2):
        raise ValueError('prime_attributes must be two different native attributes')

    stats = spec['starting_stats']
    if type(stats) is not dict:
        raise ValueError('starting_stats must be an object')
    if stats.get('mode') == 'allocated':
        exact(stats, STAT_KEYS, 'allocated starting_stats')
        plain_int(stats['points'], 65, 65, 'starting_stats.points')
        plain_int(stats['minimum'], 3, 3, 'starting_stats.minimum')
        plain_int(stats['maximum'], 18, 18, 'starting_stats.maximum')
    elif stats.get('mode') == 'random':
        exact(stats, RANDOM_KEYS, 'random starting_stats')
        ranges = stats['ranges']
        exact(ranges, ATTRIBUTES, 'random starting_stats.ranges')
        for attr in ATTRIBUTES:
            item = ranges[attr]
            exact(item, ('min', 'max'), 'range ' + attr)
            plain_int(item['min'], 3, 18, attr + '.min')
            plain_int(item['max'], 3, 18, attr + '.max')
            if item['min'] > item['max']:
                raise ValueError(attr + ': minimum exceeds maximum')
    else:
        raise ValueError('starting_stats.mode must be allocated or random')

    unlocks = spec['skill_unlocks']
    if type(unlocks) is not list or len(unlocks) > 32:
        raise ValueError('skill_unlocks must be a list of up to 32 entries')
    available = set(definition['abilities'])
    seen = set()
    for unlock in unlocks:
        exact(unlock, UNLOCK_KEYS, 'skill unlock')
        skill = unlock['skill']
        if type(skill) is not str or not SLUG.fullmatch(skill) or skill not in available:
            raise ValueError('Unlock skill must reference an ability in this class')
        if skill in seen:
            raise ValueError('Duplicate skill unlock for ' + skill)
        seen.add(skill)
        plain_int(unlock['level'], 1, 60, skill + '.level')
        plain_int(unlock['rebirth'], 0, 60, skill + '.rebirth')
    if definition['selectable'] and available != seen:
        raise ValueError('Selectable class must specify an unlock for every ability')
    return spec


def load(path, definition):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'),
                           object_pairs_hook=unique_pairs)
        return validate(definition, value)
    except (ValueError, OSError) as exc:
        raise ValueError(f'{path} — {exc}') from exc


def unlocked(spec, level, rebirth):
    plain_int(level, 1, 60, 'level')
    plain_int(rebirth, 0, 60, 'rebirth')
    return [item['skill'] for item in spec['skill_unlocks']
            if level >= item['level'] and rebirth >= item['rebirth']]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    new = sub.add_parser('new')
    new.add_argument('definition', type=Path)
    new.add_argument('output', type=Path)
    new.add_argument('--prime', choices=ATTRIBUTES, action='append', required=True)
    check = sub.add_parser('check')
    check.add_argument('definition', type=Path)
    check.add_argument('progression', type=Path)
    preview = sub.add_parser('preview')
    preview.add_argument('definition', type=Path)
    preview.add_argument('progression', type=Path)
    preview.add_argument('--level', type=int, default=1)
    preview.add_argument('--rebirth', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        definition = read(args.definition)
        if args.command == 'new':
            result = validate(definition, template(definition, args.prime))
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(canonical(result))
            print(f'Created {args.output}')
            return 0
        result = load(args.progression, definition)
        if args.command == 'check':
            print(f'PASS: class progression {definition["key"]} (draft only)')
        else:
            print('Class:', definition['name'])
            print('Prime attributes:', ', '.join(result['prime_attributes']))
            print('Starting stats:', result['starting_stats']['mode'])
            print(f'Available at level {args.level}, rebirth {args.rebirth}:',
                  ', '.join(unlocked(result, args.level, args.rebirth)) or '(none)')
            print('Native integration: NOT IMPLEMENTED')
    except (OSError, ValueError) as exc:
        print('DENIED:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
