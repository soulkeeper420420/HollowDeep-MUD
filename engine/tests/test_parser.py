#!/usr/bin/env python3
"""Exercise original command1.c parsing with fortification and boundary inputs."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
parser.add_argument('--runner')
args = parser.parse_args()
source = args.source.resolve()
article = re.search(r'char article\[\]\[10\] = \{.*?\n\};',
                    (source / 'global.c').read_text(encoding='latin-1'), re.S)
assert article, 'Original article table missing'
native_parse = re.search(r'void parse\(str, cmnd\).*?\n\}',
                         (source / 'command1.c').read_text(encoding='latin-1'), re.S)
assert native_parse, 'Original parse function missing'
fixture = r'''
#include "mstruct.h"
#include <assert.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
void parse(char *text, cmd *command);
/*ARTICLE*/
/*NATIVE_PARSE*/
struct guarded { unsigned long before; cmd command; unsigned long after; };
static int checks;
static void run(const char *text, int count, const char *last, long value) {
    struct guarded guarded;
    char *input = malloc(strlen(text) + 1);
    int i;
    assert(input);
    memset(&guarded, 0xa5, sizeof(guarded));
    guarded.before = guarded.after = 0x12345678UL;
    strcpy(input, text);
    snprintf(guarded.command.fullstr, sizeof(guarded.command.fullstr), "%s", text);
    parse(input, &guarded.command);
    assert(guarded.before == 0x12345678UL && guarded.after == 0x12345678UL);
    assert(guarded.command.num == count);
    assert(!strncmp(guarded.command.fullstr, text, sizeof(guarded.command.fullstr) - 1));
    for (i = 0; i < count; i++) assert(strnlen(guarded.command.str[i], 25) <= 20);
    if (count) {
        assert(!strcmp(guarded.command.str[count - 1], last));
        assert(guarded.command.val[count - 1] == value);
    }
    free(input);
    checks++;
}
int main(void) {
    char many[256];
    run("hbuild name Hall of the Seven Lanterns", 5, "Seven", 1);
    run("hbuild describe Seven lanterns light the quiet hall of the builders.", 5, "light", 1);
    run("one two three four five", 5, "five", 1);
    run("one two three four five six seven eight", 5, "five", 1);
    run("one two three four five 7 six", 5, "five", 7);
    run("get the sword", 2, "sword", 1);
    run("get 2 sword 3 shield", 3, "shield", 1);
    run("get##sword", 2, "sword", 1);
    run("   look   ", 1, "look", 1);
    run("", 0, "", 0);
    run("x", 1, "x", 1);
    run("abcdefghijklmnopqrstuvwx", 1, "abcdefghijklmnopqrst", 1);
    memset(many, 'a', sizeof(many) - 1); many[255] = 0;
    run(many, 1, "aaaaaaaaaaaaaaaaaaaa", 1);
    memset(many, ' ', sizeof(many) - 1);
    run(many, 0, "", 0);
    puts("PASS: original command parser word limits, selectors, terminators and full text (14 cases)");
    return 0;
}
'''.replace('/*ARTICLE*/', article.group(0)).replace('/*NATIVE_PARSE*/', native_parse.group(0))
with tempfile.TemporaryDirectory(prefix='hollowdeep-parser-test-') as temporary:
    work = Path(temporary)
    fixture_path = work / 'parser-test.c'
    fixture_path.write_text(fixture)
    executable = work / 'parser-test'
    command = [args.cc, '-std=gnu89', '-O2', '-D_FORTIFY_SOURCE=3',
               '-fstack-protector-strong', '-fcommon', '-ffunction-sections', '-fdata-sections',
               '-Wno-implicit-function-declaration', '-Wno-int-conversion',
               '-Wno-incompatible-pointer-types', '-Wno-return-type',
               '-I', str(source), str(fixture_path),
               '-Wl,--gc-sections', '-o', str(executable)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise SystemExit('Cannot compile original parser test:\n' + result.stderr[-8000:])
    subprocess.run(([args.runner] if args.runner else []) + [str(executable)], check=True, timeout=20)
