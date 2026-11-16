#!/usr/bin/env python3
"""Apply reviewed Round 73G store patch to a disposable native source COPY.

Never accepts the live MUD tree; refuses source drift or repeated patching.
No service, player or room data is read or modified by this installer.
"""
import hashlib
import pathlib
import sys

EXPECTED_FILES2 = 'd2c4390167b2c9fb1b66c6ec727e84ccbeab78dd5e5a3c50b58c23ef37850cfe'
EXPECTED_COMPRESS = '66c8fdfef649d9fd9794de7d3f0b4493d2a350f42d0c0d99331021980b26fc20'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch(src, payload_dir):
    raw_src = pathlib.Path(src)
    if raw_src.is_symlink():
        raise RuntimeError('Symlinked source directory refused')
    src = raw_src.resolve(strict=True)
    payload_dir = pathlib.Path(payload_dir).resolve(strict=True)
    if (not str(src).startswith('/root/hollowdeep-dev/') and
            not str(src).startswith('/mnt/data/round73g_native_integration/stage-test')):
        raise RuntimeError('Only disposable native source trees may be patched')
    if src == pathlib.Path('/srv/hollowdeep/world/src_3.00') or src.is_symlink():
        raise RuntimeError('Production source path refused')
    required = ['files2.c', 'compress.c', 'command8.c', 'Makefile']
    for name in required:
        f = src / name
        if not f.is_file() or f.is_symlink():
            raise RuntimeError(f'Missing or symlinked native source: {name}')
    if sha(src / 'files2.c') != EXPECTED_FILES2 or sha(src / 'compress.c') != EXPECTED_COMPRESS:
        raise RuntimeError('Native source differs from audited archive; no patch applied')
    f2 = (src / 'files2.c').read_text()
    signature = 'int save_ply(str, ply_ptr)\nchar\t\t*str;\ncreature\t*ply_ptr;\n{'
    assert f2.count(signature) == 1, 'save_ply signature mismatch'
    save_start = f2.index(signature)
    load_header = '/***********************************************************************/\n/*\t\t\t\tload_ply'
    save_end = f2.index(load_header, save_start)
    load_signature = 'int load_ply(str, ply_ptr)\nchar\t\t*str;\ncreature\t**ply_ptr;\n{'
    assert f2.count(load_signature) == 1, 'load_ply signature mismatch'
    load_start = f2.index(load_signature, save_end)
    queue_header = '/**********************************************************************/\n/*\t\t\t\tput_queue'
    load_end = f2.index(queue_header, load_start)
    f2patched = f2[:save_start] + '''int save_ply(str, ply_ptr)
char *str;
creature *ply_ptr;
{
    return hd_store_save_player(str, ply_ptr);
}

''' + f2[save_end:load_start] + '''int load_ply(str, ply_ptr)
char *str;
creature **ply_ptr;
{
    return hd_store_load_player(str, ply_ptr);
}

''' + f2[load_end:]
    include = '#include "mextern.h"\n'
    assert f2patched.count(include) == 1
    f2patched = f2patched.replace(include, include +
        '/* Private Round 73G bounded, atomic player save/load bridge. */\n'
        'extern int hd_store_save_player();\n'
        'extern int hd_store_load_player();\n', 1)
    c8 = (src / 'command8.c').read_text()
    expected = '''\tif(!dum_ptr->name[0]) return;

\tif(save_ply(dum_ptr->name, dum_ptr) < 0)
\t\tmerror("ERROR - savegame", NONFATAL);

\tfor(i=0; i<n; i++)
\t\tdel_obj_crt(obj[i], dum_ptr);

\tfree(dum_ptr);

\tprint(ply_ptr->fd, "Player saved.\\n");'''
    replacement = '''\t/* Never report success if the file write failed or durability is
\t * uncertain. Readied equipment is still detached from our copy. */
\t{
\t\tint save_status = dum_ptr->name[0] ?
\t\t\tsave_ply(dum_ptr->name, dum_ptr) : -1;
\t\tfor(i=0; i<n; i++)
\t\t\tdel_obj_crt(obj[i], dum_ptr);
\t\tfree(dum_ptr);
\t\tif(save_status < 0) {
\t\t\tmerror("ERROR - savegame", NONFATAL);
\t\t\tprint(ply_ptr->fd,
\t\t\t   "Player save not confirmed. Staff must verify before retry.\\n");
\t\t\treturn(0);
\t\t}
\t}
\tprint(ply_ptr->fd, "Player saved.\\n");'''
    if c8.count(expected) != 1:
        raise RuntimeError('command8 savegame source changed; no patch applied')
    c8patched = c8.replace(expected, replacement, 1)
    mk = (src / 'Makefile').read_text()
    marker = '\nfrp.new: $(OBJECTS)'
    if mk.count(marker) != 1 or 'hd_player_store.o' in mk or '-DCOMPRESS' not in mk:
        raise RuntimeError('Makefile differs or is already patched')
    mk = mk.replace(marker,
        '\n# Round 73G private receipt-preserving native save/load candidate\n'
        'OBJECTS += hd_player_store.o treasure_receipt.o atomic_player_snapshot.o\n'
        + marker, 1)
    if not (payload_dir / 'compress_patched.c').is_file():
        raise RuntimeError('Missing bounded compressor source')
    additions = ['hd_player_store.c', 'hd_player_store.h', 'treasure_receipt.c',
                 'treasure_receipt.h', 'atomic_player_snapshot.c',
                 'atomic_player_snapshot.h']
    for name in additions:
        if (src / name).exists() or not (payload_dir / name).is_file():
            raise RuntimeError(f'Stage already modified or missing authored file: {name}')
    # All source validation above precedes the first write.
    (src / 'files2.c').write_text(f2patched)
    (src / 'command8.c').write_text(c8patched)
    (src / 'Makefile').write_text(mk)
    (src / 'compress.c').write_bytes((payload_dir / 'compress_patched.c').read_bytes())
    for name in additions:
        (src / name).write_bytes((payload_dir / name).read_bytes())
    print('ROUND 73G: audited private native save/load patch installed')
    print('TREASURE COMMAND REWIRING: DISABLED')
    print('PRODUCTION MODIFICATIONS: NONE')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python3 apply_private.py /root/hollowdeep-dev/DISPOSABLE-STAGE /path/to/authored-package')
    patch(sys.argv[1], sys.argv[2])
