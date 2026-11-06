#!/usr/bin/env python3
"""Prepare and manage an editable, isolated original Mordor 3.00 checkout.

Uses only Python's standard library. Original engine notices are preserved.
No commands upload, deploy, or modify an existing production installation.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
ARCHIVE_URL = 'https://godwars.net/~mudbytes/files/codebases/Mordor_3.00.tar.gz'
ARCHIVE_SHA256 = '05fa24e9d475636bb77020e00a3c2b77a21516af63eef7baf6779ffc1f75e0c0'
SOURCE_DIR = 'src_3.00'
CORE = ('global files1 files2 files3 command1 command2 command3 command4 '
        'command5 command6 command7 command8 command9 command10 command11 command12 '
        'magic1 magic2 magic3 magic4 magic5 magic6 magic7 magic8 '
        'dm1 dm2 dm3 dm4 dm5 dm6 io player creature room object update post action '
        'misc special1 compress memory combat logic main hollowdeep hollowdeep_net '
        'hollowdeep_staff hollowdeep_stance').split()
EXTENSION_COMMANDS = ('hcommands', 'hclass', 'hquest', 'hprofile', 'hstaff', 'hmoderate', 'hstance')
EXTENSION_SOURCES = tuple(f'{name}.{suffix}' for name in
                          ('hollowdeep', 'hollowdeep_net', 'hollowdeep_staff', 'hollowdeep_stance')
                          for suffix in ('c', 'h'))
EXTENSION_HELP = tuple(f'help.{number}' for number in range(84, 84 + len(EXTENSION_COMMANDS)))

def replace_once(text, before, after, name):
    if text.count(before) != 1:
        raise ValueError(f'{name}: expected exactly one patch anchor; original source differs')
    return text.replace(before, after, 1)

def prepare_archive(archive, destination, admin):
    if not re.fullmatch(r'[A-Z][a-z]{2,13}', admin):
        raise ValueError('Admin must be 3–14 letters, initial capital, then lowercase, e.g. Realmkeeper.')
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Archive checksum mismatch; use the original Mordor_3.00.tar.gz distribution.')
    destination = destination.resolve()
    if destination.exists():
        raise ValueError('Destination already exists. Choose a new directory; existing saves are never overwritten.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix='.hollowdeep-prepare-', dir=destination.parent))
    try:
        # Only native source, world data, help, documentation and legal notices.
        # Old executables, player accounts, messages and runtime logs are excluded.
        allowed_roots = {SOURCE_DIR, 'rooms', 'objmon', 'help', 'docs'}
        legal = {'bin/COPYRIGHT', 'bin/DISCLAIMER', 'bin/README-FIRST', 'bin/README-Unix'}
        total = 0
        with tarfile.open(archive, 'r:gz') as bundle:
            for member in bundle:
                name = PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts or '\\' in member.name:
                    raise ValueError('Unsafe archive path')
                if not name.parts or (name.parts[0] not in allowed_roots and str(name) not in legal):
                    continue
                if member.isdir():
                    (staged / str(name)).mkdir(parents=True, exist_ok=True)
                    continue
                if member.issym() and str(name) in ('help/help.54', 'help/help.55') and member.linkname == 'help.53':
                    # The original archive aliases three help pages. Materialize
                    # the verified page as a regular file; never create links.
                    page = bundle.getmember('help/help.53')
                    if not page.isfile(): raise ValueError('Unexpected linked help target')
                    target = staged / str(name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.extractfile(page) as source:
                        target.write_bytes(source.read())
                    target.chmod(0o600)
                    continue
                if not member.isfile():
                    raise ValueError('Unexpected archive link or special file')
                total += member.size
                if member.size > 8 * 1024 * 1024 or total > 64 * 1024 * 1024:
                    raise ValueError('Archive exceeds expected extraction limits')
                target = staged / str(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, target.open('wb') as output:
                    shutil.copyfileobj(source, output)
                target.chmod(0o600)
        for name in ('player', 'player/backup', 'player/simul', 'post', 'log', 'log/auth', 'hollowdeep-data', 'bin'):
            (staged / name).mkdir(parents=True, exist_ok=True)
        (staged / 'log/news').write_text('Hollowdeep: original Mordor 3.00 with an exploration journal.\n')
        apply_compatibility(staged, admin)
        (staged / '.hollowdeep.json').write_text(json.dumps({
            'format': 1, 'archive_sha256': ARCHIVE_SHA256, 'admin': admin,
            'bits': 32, 'default_bind': '127.0.0.1', 'compatibility_revision': 2
        }, indent=2) + '\n')
        (staged / '.gitignore').write_text('*.o\nfrp.new\nplayer/\nlog/\npost/\nhollowdeep-data/\n')
        staged.rename(destination)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return destination

def apply_compatibility(work, admin):
    source = work / SOURCE_DIR
    patch = []
    def edit(name, transform):
        path = source / name
        before = path.read_text(encoding='latin-1')
        after = transform(before)
        path.write_text(after, encoding='latin-1')
        patch.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                     fromfile=f'a/{SOURCE_DIR}/{name}', tofile=f'b/{SOURCE_DIR}/{name}'))

    def types(text):
        for suffix in ('', '2', '3', '4', '5', '6', '7'):
            value = admin if not suffix else ''
            text, count = re.subn(r'(?m)^#define DMNAME' + suffix + r'\s+"[^"]*"',
                                 f'#define DMNAME{suffix}          "{value}"', text)
            if count != 1: raise ValueError('Unexpected DM name configuration')
        for macro, path in {'ROOMPATH': 'rooms', 'MONPATH': 'objmon', 'OBJPATH': 'objmon',
                           'PLAYERPATH': 'player', 'DOCPATH': 'help', 'POSTPATH': 'post',
                           'BINPATH': 'bin', 'LOGPATH': 'log'}.items():
            text, count = re.subn(r'(?m)^#define ' + macro + r'\s+"[^"]*"',
                                 f'#define {macro} "{path}"', text)
            if count != 1: raise ValueError('Unexpected runtime path configuration')
        return text
    edit('mtype.h', types)
    def declarations(text):
        text = replace_once(text, '#include <stdio.h>',
            '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n#include <time.h>\n#include <sys/stat.h>\n#include <fcntl.h>', 'mextern includes')
        # Match the five-element definition in global.c and update_weather's
        # five iterations; modern optimizers otherwise infer out-of-bounds UB.
        return replace_once(text, 'Weather[4]', 'Weather[5]', 'weather declaration')
    edit('mextern.h', declarations)
    def updates(text):
        # Use literal lengths; the original constants read beyond both strings.
        for message, length in ((r'\n\rThe Watcher has locked your account.\n\r', 42),
                                (r'\n\rSend questions to auth@moria.bio.uci.edu.\n\r', 46)):
            text = replace_once(text, f'"{message}", {length});',
                                f'"{message}", sizeof("{message}") - 1);', 'lockout message length')
        return text
    edit('update.c', updates)
    def main(text):
        text = replace_once(text, '\tstatic void mvc_log();\n\tstatic int schedule_g();', '', 'main declarations')
        text = replace_once(text, 'int Port;', 'static void mvc_log();\nstatic int schedule_g();\nint Port;', 'main prototypes')
        return text.replace('umask(000);', 'umask(077);')
    edit('main.c', main)
    def dm(text):
        text = replace_once(text, 'static int\tdm_gspells();', '', 'dm declaration')
        return replace_once(text, '#include "mstruct.h"', '#include "mstruct.h"\nstatic int dm_gspells();', 'dm prototype')
    edit('dm4.c', dm)
    def login(text):
        text = replace_once(text, '#include "mstruct.h"',
                            '#include "mstruct.h"\n#include "hollowdeep_staff.h"', 'staff dispatch include')
        text = replace_once(text,
            'print(fd, "\\nChoose a password (up to 14 chars): ");',
            'print(fd, "%c%c%c\\nChoose a password (up to 14 chars): ", 255, 251, 1);',
            'new character password echo')
        text = replace_once(text, 'strncpy(Ply[fd].ply->password, str, 14);',
            'strncpy(Ply[fd].ply->password, str, 14);\n\t\tprint(fd, "%c%c%c", 255, 252, 1);',
            'new character echo restoration')
        text = replace_once(text, r'"\255\252\1\n\rIncorrect.\n\r"',
                            r'"\377\374\1\n\rIncorrect.\n\r"', 'failed login echo restoration')
        return replace_once(text, '\tif(cmdlist[cmdno].cmdno < 0)',
            '\t/* Apply moderation after alias resolution, before every native dispatch. */\n'
            '\tif(hd_staff_blocks_command(Ply[fd].ply, cmdlist[cmdno].cmdno)) return 0;\n\n'
            '\tif(cmdlist[cmdno].cmdno < 0)', 'staff chat gate')
    edit('command1.c', login)
    def physical_attacks(text, player_attack):
        text = replace_once(text, '#include "mstruct.h"',
                            '#include "mstruct.h"\n#include "hollowdeep_stance.h"', 'stance include')
        before = 'n = ply_ptr->thaco - crt_ptr->armor/10;' if player_attack else 'n = crt_ptr->thaco - att_ptr->armor/10;'
        after = ('n = hd_stance_threshold(ply_ptr, crt_ptr, ply_ptr->thaco - crt_ptr->armor/10);'
                 if player_attack else
                 'n = hd_stance_threshold(crt_ptr, att_ptr, crt_ptr->thaco - att_ptr->armor/10);')
        expected = 1 if player_attack else 2
        if text.count(before) != expected:
            raise ValueError('Physical attack hooks differ from the original source')
        return text.replace(before, after)
    edit('command5.c', lambda text: physical_attacks(text, True))
    edit('combat.c', lambda text: physical_attacks(text, False))
    def io(text):
        text = replace_once(text, '#include "mextern.h"',
                            '#include "mextern.h"\n#include "hollowdeep_net.h"', 'network parser include')
        text = replace_once(text, 'addr.sin_addr.s_addr = INADDR_ANY;',
            '/* Explicit binding: loopback unless the launcher opts into public access. */\n'
            '\taddr.sin_addr.s_addr = inet_addr(getenv("HOLLOWDEEP_BIND") ? getenv("HOLLOWDEEP_BIND") : "127.0.0.1");', 'listening address') if text.count('addr.sin_addr.s_addr = INADDR_ANY;') == 1 else text.replace(
            'addr.sin_addr.s_addr = INADDR_ANY;',
            '/* Listening socket defaults to loopback; peer address is filled by accept(). */\n'
            '\taddr.sin_addr.s_addr = inet_addr(getenv("HOLLOWDEEP_BIND") ? getenv("HOLLOWDEEP_BIND") : "127.0.0.1");', 1)
        text = text.replace('signal(SIGTERM, SIG_IGN);', 'signal(SIGTERM, SIG_DFL);')
        text = text.replace('if(fd < 0 || fd > Tablesize)', 'if(fd < 0 || fd >= Tablesize)')
        text = replace_once(text, '\tif (fd < 0)\n\t\tmerror("accept_connect", FATAL);',
            '\tif (fd < 0) return;\n\tif (fd >= Tablesize || fd >= PMAX) { close(fd); return; }\n\thd_net_reset(fd);', 'accept bounds')
        # Obsolete ident lookups are optional, not part of development startup.
        start = text.index('#ifndef WIN32\n#ifdef IRIX\n        pid = fork();', text.index('void accept_connect()'))
        end = text.index('\n\tFD_SET(fd, &Sockets);', start)
        text = text[:start] + '\tstrcpy(io->userid, "unknown");\n\tio->lookup_pid = 0;\n' + text[end:]
        text = replace_once(text, '\tFD_CLR(fd, &Sockets);',
                            '\thd_net_reset(fd);\n\tFD_CLR(fd, &Sockets);', 'disconnect parser reset')
        # Normalize the Telnet stream before the legacy command buffer. Parser
        # state survives read boundaries without touching serialized game types.
        text = replace_once(text, '\tchar \tbuf[128], lastchar;',
                            '\tchar \tbuf[128];\n\tint normalized, lastchar;', 'input byte state')
        text = replace_once(text, '\tif(n<=0)\n\t\tPly[fd].io->commands = -1;',
            '\tif(n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) return 0;\n'
            '\tif(n<=0)\n\t\tPly[fd].io->commands = -1;', 'nonblocking read handling')
        text = replace_once(text, '\t\tlastchar = 0;', '\t\tlastchar = -1;', 'input sentinel')
        text = replace_once(text,
            "\t\tfor(i=0; i<n; i++) {\n\t\t\tif(buf[i] > 31 || (buf[i] == '\\n' && lastchar != '\\r')\n\t\t\t    || buf[i] == '\\r' || buf[i] == '\\b') {",
            "\t\tfor(i=0; i<n; i++) {\n\t\t\tnormalized = hd_net_feed(fd, (unsigned char)buf[i]);\n"
            "\t\t\tif(normalized < 0) continue;\n\t\t\tbuf[i] = (char)normalized;\n"
            "\t\t\tif(buf[i] > 31 || buf[i] == '\\n' || buf[i] == '\\b') {", 'Telnet input filtering')
        text = replace_once(text, "\t\tif(buf[n-1] == '\\n' || buf[n-1] == '\\r')",
                            "\t\tif(lastchar == '\\n')", 'normalized prompt boundary')
        text = replace_once(text, '\t\telse\n\t\t\tPly[fd].io->intrpt &= ~1;',
                            '\t\telse if(lastchar >= 0)\n\t\t\tPly[fd].io->intrpt &= ~1;', 'protocol-only prompt state')
        return text
    edit('io.c', io)
    def globals_(text):
        text = replace_once(text, '#include "mstruct.h"',
                            '#include "mstruct.h"\n#include "hollowdeep.h"\n#include "hollowdeep_staff.h"\n#include "hollowdeep_stance.h"',
                            'extension include')
        anchor = '\t{ "touch", 83, touch_of_death},'
        return replace_once(text, anchor, anchor + '\n' + ''.join(
            f'\t{{ "{command}", {number}, {command} }},\n'
            for number, command in enumerate(EXTENSION_COMMANDS, 84)), 'command table')
    edit('global.c', globals_)
    original_make = (source / 'Makefile').read_text()
    makefile = ('# Hollowdeep development build of original Mordor 3.00. Original notices retained.\n'
                'CC ?= cc\n'
                'CFLAGS = -m32 -std=gnu89 -O1 -g -fcommon -DDEBUG -DCOMPRESS '
                '-Wno-implicit-function-declaration -Wno-int-conversion '
                '-Wno-incompatible-pointer-types -Wno-return-type\n'
                'LDFLAGS = -m32\nLDLIBS = -lm\n'
                'OBJECTS = ' + ' '.join(f'{name}.o' for name in CORE) + '\n\n'
                'frp.new: $(OBJECTS)\n\t$(CC) $(LDFLAGS) $(OBJECTS) -o $@ $(LDLIBS)\n'
                '%.o: %.c mstruct.h mtype.h mextern.h hollowdeep.h hollowdeep_net.h hollowdeep_staff.h hollowdeep_stance.h\n\t$(CC) $(CFLAGS) -c $< -o $@\n'
                'clean:\n\trm -f $(OBJECTS) frp.new\n.PHONY: clean\n')
    (source / 'Makefile').write_text(makefile)
    patch.extend(difflib.unified_diff(original_make.splitlines(True), makefile.splitlines(True),
                 fromfile=f'a/{SOURCE_DIR}/Makefile', tofile=f'b/{SOURCE_DIR}/Makefile'))
    for name in EXTENSION_SOURCES:
        shutil.copy2(ROOT / 'extensions' / name, source / name)
    for name in EXTENSION_HELP:
        shutil.copy2(ROOT / 'extensions' / name, work / 'help' / name)
    (work / 'hollowdeep-compatibility.patch').write_text(''.join(patch))

def load_work(path):
    path = path.resolve()
    try: config = json.loads((path / '.hollowdeep.json').read_text())
    except (OSError, ValueError): raise ValueError('Not a prepared Hollowdeep checkout; run prepare first.')
    if config.get('format') != 1 or config.get('archive_sha256') != ARCHIVE_SHA256:
        raise ValueError('Unrecognized checkout metadata')
    return path, config

def build(work, compiler, runner=None):
    work, _ = load_work(work)
    # Stop before producing an ABI-incompatible executable on 64-bit systems.
    with tempfile.TemporaryDirectory(prefix='hollowdeep-abi-') as temp:
        check = Path(temp) / 'check.c'
        check.write_text('#include <stdio.h>\nint main(void) { return sizeof(void*) != 4 || sizeof(long) != 4; }\n')
        result = subprocess.run([compiler, '-m32', str(check), '-o', str(Path(temp) / 'check')], capture_output=True, text=True)
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            raise ValueError('A 32-bit C toolchain is required. On Debian/Ubuntu install gcc-multilib and libc6-dev-i386, then retry. No game files were changed.')
        command = [str(Path(temp) / 'check')]
        if runner: command.insert(0, runner)
        try:
            subprocess.run(command, check=True)
        except OSError as exc:
            raise ValueError('The compiler produced a 32-bit executable, but this host cannot run it. '
                             'Use a Linux host with i386 execution support, or supply --runner /path/to/qemu-i386.') from exc
    subprocess.run(['make', '-C', str(work / SOURCE_DIR), '-j2', f'CC={compiler}'], check=True)
    return work / SOURCE_DIR / 'frp.new'

def sync_extensions(work):
    """Explicitly copy edited kit files into a prepared source tree, backing up changes."""
    work, _ = load_work(work)
    source_dir = work / SOURCE_DIR
    makefile = (source_dir / 'Makefile').read_text()
    dispatch = (source_dir / 'command1.c').read_text(encoding='latin-1')
    table = (source_dir / 'global.c').read_text(encoding='latin-1')
    hooks = ((source_dir / 'command5.c').read_text(encoding='latin-1').count('hd_stance_threshold('),
             (source_dir / 'combat.c').read_text(encoding='latin-1').count('hd_stance_threshold('))
    if (any(f'{name}.o' not in makefile for name in ('hollowdeep_net', 'hollowdeep_staff', 'hollowdeep_stance'))
            or 'hd_staff_blocks_command(' not in dispatch or hooks != (1, 2)
            or any(f'{{ "{command}", {number}, {command} }}' not in table
                   for number, command in enumerate(EXTENSION_COMMANDS, 84))):
        raise ValueError('This checkout predates the staff and combat-stance hooks. Use the guarded '
                         'native updater or prepare a separate fresh checkout; keep the existing world and saves intact.')
    changes = []
    for name in EXTENSION_SOURCES + EXTENSION_HELP:
        target = work / (SOURCE_DIR if name.endswith(('.c', '.h')) else 'help') / name
        source = ROOT / 'extensions' / name
        if not source.is_file() or source.is_symlink() or target.is_symlink():
            raise ValueError('Expected regular extension files; refusing a symlink or missing source.')
        if not target.exists() or target.read_bytes() != source.read_bytes():
            changes.append((source, target))
    if not changes:
        print('Extensions already match this kit.')
        return
    backup = Path(tempfile.mkdtemp(prefix='extension-backup-', dir=work))
    for source, target in changes:
        if target.exists(): shutil.copy2(target, backup / target.name)
        shutil.copy2(source, target)
    print(f'Synced {len(changes)} extension files. Previous files: {backup}. Build and test before restarting.')

def run_server(work, port, public, runner=None):
    work, config = load_work(work)
    if not 1024 <= port <= 65535: raise ValueError('Choose a port from 1024 to 65535.')
    executable = work / SOURCE_DIR / 'frp.new'
    if not executable.is_file(): raise ValueError('No built engine found; run build first.')
    if public and not (work / 'player' / config['admin']).is_file():
        raise ValueError('Create your configured admin character over localhost before opting into public access.')
    env = os.environ.copy()
    env['HOLLOWDEEP_BIND'] = '0.0.0.0' if public else '127.0.0.1'
    print(f'Running original Mordor 3.00 on {env["HOLLOWDEEP_BIND"]}:{port}. Stop with Ctrl+C; use in-game save/quit before shutdown.', flush=True)
    os.chdir(work)
    command = [str(executable), str(port), '-r']
    if runner: command.insert(0, runner)
    os.execvpe(command[0], command, env)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fetch = commands.add_parser('fetch', help='Fetch the checksum-pinned original distribution')
    fetch.add_argument('--output', type=Path, required=True)
    prepare = commands.add_parser('prepare', help='Create a fresh editable checkout; never overwrite a world')
    prepare.add_argument('--archive', type=Path, required=True)
    prepare.add_argument('--destination', type=Path, required=True)
    prepare.add_argument('--admin', required=True)
    build_parser = commands.add_parser('build', help='Build the original 32-bit engine')
    build_parser.add_argument('--work', type=Path, required=True)
    build_parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
    build_parser.add_argument('--runner', help='Optional i386 execution helper, e.g. /usr/bin/qemu-i386')
    sync = commands.add_parser('sync-extensions', help='Copy edited kit extensions into prepared source, retaining backups')
    sync.add_argument('--work', type=Path, required=True)
    run = commands.add_parser('run', help='Run in foreground on localhost by default')
    run.add_argument('--work', type=Path, required=True)
    run.add_argument('--port', type=int, default=4040)
    run.add_argument('--public', action='store_true', help='Bind all IPv4 interfaces after local admin creation')
    run.add_argument('--runner', help='Optional i386 execution helper, e.g. /usr/bin/qemu-i386')
    args = parser.parse_args()
    try:
        if args.command == 'fetch':
            if args.output.exists(): raise ValueError('Output already exists; verify or choose another path.')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(ARCHIVE_URL, timeout=30) as response:
                data = response.read(8 * 1024 * 1024 + 1)
            if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256: raise ValueError('Downloaded archive checksum mismatch.')
            args.output.write_bytes(data)
            print(f'Verified original distribution: {args.output}')
        elif args.command == 'prepare': print(f'Prepared fresh original-engine checkout: {prepare_archive(args.archive, args.destination, args.admin)}')
        elif args.command == 'build': print(f'Built: {build(args.work, args.cc, args.runner)}')
        elif args.command == 'sync-extensions': sync_extensions(args.work)
        else: run_server(args.work, args.port, args.public, args.runner)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Error: {exc}\n')

if __name__ == '__main__': main()
