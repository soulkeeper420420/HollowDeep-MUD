#!/usr/bin/env python3
"""Export native character entries and preview supported C source changes."""
import argparse
import difflib
import json
from pathlib import Path
import re
import sys

from content import ATTRIBUTES, canonical, read, template, validate


SYMBOLS = {
    'class': dict(zip(
        ('assassin', 'barbarian', 'cleric', 'fighter', 'mage', 'paladin',
         'ranger', 'thief', 'bard', 'monk'),
        ('ASSASSIN', 'BARBARIAN', 'CLERIC', 'FIGHTER', 'MAGE', 'PALADIN',
         'RANGER', 'THIEF', 'BARD', 'MONK'))),
    'race': dict(zip(
        ('dwarf', 'elf', 'half-elf', 'hobbit', 'human', 'orc', 'half-giant',
         'gnome', 'troll', 'half-orc', 'ogre', 'dark-elf', 'goblin'),
        ('DWARF', 'ELF', 'HALFELF', 'HOBBIT', 'HUMAN', 'ORC', 'HALFGIANT',
         'GNOME', 'TROLL', 'HALFORC', 'OGRE', 'DARKELF', 'GOBLIN'))),
}
LITERAL = r'"(?:[^"\\\n]|\\["\\])*"'
RACE_SWITCH = r'switch\(Ply\[fd\]\.ply->race\)\s*\{(?P<body>[^{}]*)\n\t\t\}'
RACE_CASE = r'^[ \t]*case ([A-Z]+):[ \t]*\n(.*?)^[ \t]*break;[ \t]*$'
STAT = (r'Ply\[fd\]\.ply->(' + '|'.join(ATTRIBUTES) +
        r')\s*(\+\+|--|\+=\s*\d+|-=\s*\d+)\s*;')


def one(pattern, source, label, flags=0):
    matches = list(re.finditer(pattern, source, flags))
    if len(matches) != 1:
        raise ValueError(f'Expected one supported {label} in the source')
    return matches[0]


def native_entry(source, kind, key):
    if key not in SYMBOLS[kind]:
        raise ValueError(f'Unknown native {kind} {key!r}. Available: {", ".join(SYMBOLS[kind])}')
    symbol = SYMBOLS[kind][key]
    header = (source / 'mtype.h').read_text(encoding='latin-1')
    index = int(one(rf'^#define\s+{symbol}\s+(\d+)\b', header, symbol, re.M)[1])
    global_source = (source / 'global.c').read_text(encoding='latin-1')
    table_pattern = rf'char {kind}_str\[\]\[15\]\s*=\s*\{{(?P<rows>[^{{}}]*)\}};'
    table = one(table_pattern, global_source, f'{kind} labels')
    rows = table['rows']
    if not re.fullmatch(rf'\s*{LITERAL}(?:\s*,\s*{LITERAL})*\s*,?\s*', rows):
        raise ValueError(f'Unsupported entries in {kind} labels')
    entries = list(re.finditer(LITERAL, rows))
    if not 0 < index < len(entries):
        raise ValueError(f'Native {symbol} index falls outside the label table')
    entry = entries[index]
    labels = [json.loads(item[0]) for item in entries]
    value = template(kind, key, labels[index])
    value['description'] = f'Existing HollowDeep {kind} {key}.'
    value['selectable'] = True
    locations = {'name': ('global.c', global_source,
                               table.start('rows') + entry.start(),
                               table.start('rows') + entry.end())}

    if kind == 'race':
        command_source = (source / 'command1.c').read_text(encoding='latin-1')
        switch = one(RACE_SWITCH, command_source, 'race attribute switch')
        case = one(RACE_CASE.replace('([A-Z]+)', f'({symbol})'),
                   switch['body'], f'{symbol} attribute case', re.M | re.S)
        statements = case[2]
        assignments = list(re.finditer(STAT, statements))
        if re.sub(STAT, '', statements).strip():
            raise ValueError(f'Unsupported statements in {symbol} attribute case')
        seen = set()
        for field, operation in (match.groups() for match in assignments):
            if field in seen:
                raise ValueError(f'Repeated assignment to {field} in {symbol}')
            seen.add(field)
            amount = 1 if operation in ('++', '--') else int(operation[2:].strip())
            value['attributes'][field] = amount if operation.startswith('+') else -amount
        locations['attributes'] = ('command1.c', command_source, switch.start('body') + case.start(2),
                                  switch.start('body') + case.end(2))

    else:
        stats = one(r'class_stats\[13\]\s*=\s*\{(.*?)\n\};',
                    global_source, 'class growth table', re.S)
        entries = list(re.finditer(r'\{(\s*\d+(?:\s*,\s*\d+){6}\s*)\}', stats[1]))
        if len(entries) != 13 or index >= len(entries) or re.sub(r'/\*.*?\*/|\{[^{}]*\}|[\s,]', '', stats[1], flags=re.S):
            raise ValueError('Unexpected layout in class growth table')
        row = entries[index]
        fields = list(re.finditer(r'\d+', row[1]))
        for field, position in (('hp_per_level', 2), ('mp_per_level', 3)):
            number = fields[position]
            start = stats.start(1) + row.start(1) + number.start()
            locations[field] = ('global.c', global_source, start, start + len(number[0]))
            value['training'][field] = int(number[0])

    validate(value)
    return value, locations, labels, index


def native_diff(source, draft):
    original, locations, labels, index = native_entry(source, draft['kind'], draft['key'])
    allowed = {'name', 'attributes'} if draft['kind'] == 'race' else {'name', 'training'}
    unsupported = [key for key in original if key not in allowed and original[key] != draft[key]]
    if unsupported:
        raise ValueError('Native preview cannot apply: ' + ', '.join(unsupported))
    replacements = {}
    if draft['name'] != original['name']:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 '\-]{0,13}", draft['name']):
            raise ValueError('Native labels need 1–14 letters, digits, spaces, apostrophes or hyphens')
        if any(draft['name'].casefold() == label.casefold()
               for row, label in enumerate(labels) if row != index):
            raise ValueError('That native display label is already in use')
        replacements['name'] = json.dumps(draft['name'])
    if draft['attributes'] != original['attributes']:
        if any(not -2 <= offset <= 2 for offset in draft['attributes'].values()):
            raise ValueError('Native race offsets must stay within the existing -2 to +2 range')
        replacements['attributes'] = ''.join(
            f'\t\t\tPly[fd].ply->{field} {"+" if offset > 0 else "-"}= {abs(offset)};\n'
            for field, offset in draft['attributes'].items() if offset)
    if draft['kind'] == 'class':
        for field, growth in draft['training'].items():
            if growth != original['training'][field]:
                minimum = 1 if field == 'hp_per_level' else 0
                if not minimum <= growth <= 10:
                    raise ValueError(f'Native {field} must be between {minimum} and 10')
                replacements[field] = str(growth)

    files = {}
    for field, replacement in replacements.items():
        filename, body, start, end = locations[field]
        files.setdefault(filename, (body, []))[1].append((start, end, replacement))
    patches = []
    for filename, (body, changes) in files.items():
        updated = body
        for start, end, replacement in sorted(changes, reverse=True):
            updated = updated[:start] + replacement + updated[end:]
        patches.extend(difflib.unified_diff(body.splitlines(keepends=True),
                                          updated.splitlines(keepends=True),
                                          fromfile=f'a/{filename}', tofile=f'b/{filename}'))
    return ''.join(patches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    export = commands.add_parser('export')
    export.add_argument('source', type=Path)
    export.add_argument('kind', choices=SYMBOLS)
    export.add_argument('key')
    export.add_argument('output', type=Path)
    preview = commands.add_parser('preview')
    preview.add_argument('source', type=Path)
    preview.add_argument('draft', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'export':
            data, _, _, _ = native_entry(args.source, args.kind, args.key)
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(canonical(data))
            print(f'Created {args.output}')
        else:
            patch = native_diff(args.source, read(args.draft))
            print(patch or 'No native source changes.', end='' if patch else '\n')
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
