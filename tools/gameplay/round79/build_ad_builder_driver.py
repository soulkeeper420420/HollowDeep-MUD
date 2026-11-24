#!/usr/bin/env python3
"""Adapt the legacy isolated builder driver to the private native creation UI.

Only emits a fresh private copy. Never modifies the accepted helper or engine.
"""
import argparse
from pathlib import Path
from build_ad_combat_socket_replay import once


def build(text):
    text=once(text, 'elif "54 points" in low and "stats" in low:',
                'elif ("54 points" in low or "65 total points" in low) and "stats" in low:')
    text=once(text,'        elif "weapons proficiency" in low:',
              '        elif "enable ansi colors and colored status" in low:\n'
              '            answer = "no"\n'
              '        elif "weapons proficiency" in low:')
    return once(text,'def in_game(text):\n    return bool(re.search(',
                'def in_game(text):\n'
                '    clean = re.sub(r"\\x1b\\[[0-9;]*[A-Za-z]", "", text)\n'
                '    if re.search(r"HP\\s+\\d+/\\d+\\s*\\|.*MP\\s+\\d+/\\d+", clean):\n'
                '        return True\n'
                '    return bool(re.search(')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accepted_driver',type=Path)
    parser.add_argument('private_copy',type=Path)
    args=parser.parse_args()
    if args.private_copy.exists(): raise ValueError('Fresh private copy required')
    source=build(args.accepted_driver.read_text(encoding='utf-8'))
    compile(source,'<private-builder-driver>','exec')
    args.private_copy.write_text(source,encoding='utf-8')


if __name__=='__main__': main()
