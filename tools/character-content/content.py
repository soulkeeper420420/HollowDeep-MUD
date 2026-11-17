#!/usr/bin/env python3
"""Create, validate, and preview HollowDeep character content definitions."""
import argparse
import difflib
import json
from pathlib import Path
import re
import sys


ATTRIBUTES = ('strength', 'dexterity', 'constitution', 'intelligence', 'piety')
TRAINING = ('hp_per_level', 'mp_per_level')
SLUG = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')


def template(kind, key, name):
    shared = {'kind': kind, 'key': key, 'name': name, 'description': '',
              'attributes': dict.fromkeys(ATTRIBUTES, 0), 'selectable': False}
    if kind == 'race':
        return {**shared, 'traits': [], 'allowed_classes': []}
    return {**shared, 'abilities': [], 'starting_equipment': [],
            'training': dict.fromkeys(TRAINING, 0)}


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate field {key!r}')
        result[key] = value
    return result


def read(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_pairs)
        validate(value)
    except (OSError, ValueError) as exc:
        raise ValueError(f'{path} — {exc}') from exc
    return value


def require_fields(value, expected, label):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(f'{label} must contain exactly {", ".join(expected)}')


def validate_key(value, label):
    if not isinstance(value, str) or len(value) > 48 or not SLUG.fullmatch(value):
        raise ValueError(f'{label} must be a lowercase key such as deep-dwarf')


def references(value, label):
    if not isinstance(value, list):
        raise ValueError(f'{label} must be a list')
    seen = set()
    for entry in value:
        validate_key(entry, label)
        if entry in seen:
            raise ValueError(f'{label} repeats {entry!r}')
        seen.add(entry)


def numbers(value, keys, low, high, label):
    require_fields(value, keys, label)
    for key in keys:
        if type(value[key]) is not int or not low <= value[key] <= high:
            raise ValueError(f'{label}.{key} must be an integer from {low} to {high}')


def validate(value):
    if type(value) is not dict or value.get('kind') not in ('race', 'class'):
        raise ValueError('kind must be race or class')
    kind = value['kind']
    require_fields(value, template(kind, '', ''), kind)
    validate_key(value['key'], 'key')
    name = value['name']
    if (not isinstance(name, str) or not 1 <= len(name) <= 40 or name != name.strip()
            or any(not 32 <= ord(char) <= 126 for char in name)):
        raise ValueError('name must be 1–40 printable ASCII characters without outer spaces')
    if not isinstance(value['description'], str) or len(value['description']) > 2000:
        raise ValueError('description must be text of at most 2,000 characters')
    if type(value['selectable']) is not bool:
        raise ValueError('selectable must be true or false')
    if value['selectable'] and not value['description'].strip():
        raise ValueError('selectable entries need a description')
    numbers(value['attributes'], ATTRIBUTES, -34, 34, 'attributes')
    if kind == 'race':
        references(value['traits'], 'traits')
        references(value['allowed_classes'], 'allowed_classes')
    else:
        references(value['abilities'], 'abilities')
        references(value['starting_equipment'], 'starting_equipment')
        numbers(value['training'], TRAINING, 0, 32767, 'training')


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    create = commands.add_parser('new', help='write a draft definition')
    create.add_argument('kind', choices=['race', 'class'])
    create.add_argument('key')
    create.add_argument('name')
    create.add_argument('output', type=Path)
    check = commands.add_parser('check', help='validate a definition')
    check.add_argument('file', type=Path)
    preview = commands.add_parser('preview', help='review a new or edited definition')
    preview.add_argument('file', type=Path)
    preview.add_argument('--against', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == 'new':
            value = template(args.kind, args.key, args.name)
            validate(value)
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(canonical(value))
            print(f'Created {args.output}')
        else:
            value = read(args.file)
            if args.action == 'check':
                print(f'PASS: {value["kind"]} {value["key"]}')
                return 0
            before = read(args.against) if args.against else None
            if before and (before['kind'], before['key']) != (value['kind'], value['key']):
                raise ValueError('editing an existing definition requires the same kind and key')
            diff = ''.join(difflib.unified_diff(
                canonical(before).splitlines(keepends=True) if before else [],
                canonical(value).splitlines(keepends=True),
                fromfile=str(args.against) if before else '/dev/null', tofile=str(args.file)))
            print(diff or 'No definition changes.', end='' if diff else '\n')
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
