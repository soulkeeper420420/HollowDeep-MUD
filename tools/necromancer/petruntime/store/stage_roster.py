#!/usr/bin/env python3
"""Stage roster save support into a new private copy of the pinned runtime source."""
import argparse
import hashlib
from pathlib import Path
import shutil

EXPECTED = {
    'hd_player_store.c': '36be86735ec7061977c385c0a419e568ad4ec4daa3d639cff5da11278546acc4',
    'hd_pet_store.inc': '504b9500752b0d9eaf5b462638871faa46880eb272cc86dc4fb7d9c49938a59e',
    'treasure_receipt.c': 'aa6fe16fe2d789b39d0e15c195c201f197c72e831004700bbea4a8e4c92ea805',
    'treasure_receipt.h': 'c36fcfa5f5240f69e1b2772fbd2fc7373b18c8c02da14581f18c1b9832909dec',
}


def replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Patch anchor changed: ' + old)
    return source.replace(old, new)


def stage(source, target):
    source = source.resolve(strict=True)
    target = target.resolve()
    if target.exists() or target.is_relative_to(source):
        raise ValueError('Use a new destination outside the input tree')
    if any(path.is_symlink() for path in source.rglob('*')):
        raise ValueError('Input source contains symlinks')
    for name, expected in EXPECTED.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Runtime source fingerprint mismatch: ' + name)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('*.o', 'frp.new'))

    def patch(name, replacements):
        path = target / name
        body = path.read_text()
        for old, new in replacements:
            body = replace(body, old, new)
        path.write_text(body)

    patch('treasure_receipt.h', [
        ('#include <stddef.h>', '#include <stddef.h>\n#include "hd_pet_roster.h"'),
        ('HD_RECEIPT_ENTRY_BYTES + 4U)', 'HD_RECEIPT_ENTRY_BYTES + HD_ROSTER_WIRE_MAX + 4U)'),
        ('    size_t count;', '    size_t count, roster_size;\n'
         '    unsigned char roster[HD_ROSTER_WIRE_MAX];'),
    ])
    patch('treasure_receipt.c', [
        ('set->count > HD_RECEIPT_MAX)', 'set->count > HD_RECEIPT_MAX ||\n'
         '        set->roster_size > sizeof set->roster)'),
        ('if (set->count == 0)', 'if (set->count == 0 && !set->roster_size)'),
        ('HD_RECEIPT_ENTRY_BYTES * set->count;', 'HD_RECEIPT_ENTRY_BYTES * set->count + set->roster_size;'),
        ('    raw[off + 5U]', "    if (set->roster_size) raw[off + 4U] = '2';\n    raw[off + 5U]"),
        ('    crc = hd_crc', '    memcpy(raw + off, set->roster, set->roster_size);\n'
         '    off += set->roster_size;\n    crc = hd_crc'),
        ('    uint32_t stored;', '    uint32_t stored;\n    int has_roster;'),
        ('memcmp(raw + native_used, hd_magic, sizeof hd_magic)) return -1;',
         "memcmp(raw + native_used, hd_magic, 4)) return -1;\n"
         "    has_roster = raw[native_used + 4U] == '2';\n"
         "    if (!has_roster && raw[native_used + 4U] != '1') return -1;"),
        ('if (!n || n > HD_RECEIPT_MAX)', 'if ((!n && !has_roster) || n > HD_RECEIPT_MAX)'),
        ('    if (length != expected) return -1;',
         '    if (has_roster) {\n'
         '        if (length <= expected || length - expected > sizeof parsed.roster) return -1;\n'
         '        parsed.roster_size = length - expected;\n'
         '        expected = length;\n'
         '    }\n    if (length != expected) return -1;'),
        ('    if (!hd_valid(&parsed))', '    memcpy(parsed.roster, raw + off, parsed.roster_size);\n'
         '    if (!hd_valid(&parsed))'),
    ])
    patch('hd_player_store.c', [
        ('#include "hd_pet_store.inc"', '#include "hd_pet_store.inc"\n#include "hd_roster_store.inc"'),
    ])
    patch('hd_pet_store.inc', [
        ('&& pet_check_owner(raw,&set)){', '&& pet_check_owner(raw,&set) && !set.roster_size){'),
        ('|| !pet_check_owner(raw,&set)) goto done;',
         '|| !pet_check_owner(raw,&set) || set.roster_size) goto done;'),
    ])
    here = Path(__file__).resolve().parent
    patch('hd_player_store.c', [
        ('static int reserved_receipt(const char *claim)',
         'static const char conjure_id[] = '
         '"ffffffffffffffffffffffffffffff77";\n\n'
         'static int reserved_receipt(const char *claim)'),
        ('|| !strcmp(claim, pet_id);',
         '|| !strcmp(claim, pet_id) || !strcmp(claim, conjure_id);'),
        ('#include "hd_roster_store.inc"',
         '#include "hd_roster_store.inc"\n#include "hd_conjure_store.inc"'),
    ])
    for name in ('hd_conjure.h', 'hd_conjure.c', 'hd_conjure_store.inc'):
        shutil.copyfile(here.parent / 'conjure' / name, target / name)

    for name in ('hd_pet_roster.h', 'hd_pet_roster.c'):
        shutil.copyfile(here.parent / 'roster' / name, target / name)
    shutil.copyfile(here / 'hd_roster_store.inc', target / 'hd_roster_store.inc')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    stage(args.source, args.target)
