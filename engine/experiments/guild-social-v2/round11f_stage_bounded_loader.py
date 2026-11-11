#!/usr/bin/env python3
"""Round 11F private-only bounded native loader / corrupt-account guard.

Requires fresh copy of already tested Round11D source; all modifications are
made only inside round11-load-*/src. No live MUD or player files are touched.
"""
import re
from pathlib import Path
import sys

HOME = Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv) != 2:
    raise SystemExit("STOP: Supply new private Round11F source directory")
src = Path(sys.argv[1]).resolve(strict=True)
if (src.name != "src" or src.parent.parent != HOME
        or not src.parent.name.startswith("round11-load-")):
    raise SystemExit("STOP: Path is not a new private Round11F source directory")
for name in ("files2.c", "compress.c", "command1.c", "Makefile"):
    p = src/name
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Missing or symlinked private file " + name)

path_files = src/"files2.c"
path_lzw = src/"compress.c"
path_login = src/"command1.c"
files = path_files.read_text()
lz = path_lzw.read_text()
login = path_login.read_text()

for label, valid in [
    ("Round11D bounded saver", "HD11_SAVE_RAW_LIMIT" in files and
        "hd11_atomic_player_write" in files),
    ("Round11D LZW output bound", "hd11_compress_bounded" in lz and
        "hd11_lzw_cap" in lz),
    ("unmodified old loader", files.count("int load_ply(str, ply_ptr)") == 1
        and "size = read(fd, a_buf, 50000);" in files),
    ("Round11D final load format", files.count("read_crt_from_mem(b_buf, *ply_ptr, 0)") == 1),
    ("unmodified native login", "hd11_existing_character_unreadable" not in login),
]:
    if not valid:
        raise SystemExit("STOP: "+label+" not proven")

# Patch only the decoder portion of the compression unit, not the tested
# encoder or the existing bounded compressor used by Round11D.
marker = "int uncompress(in, out, size)"
if lz.count(marker) != 1:
    raise SystemExit("STOP: Native decoder entry not unique")
before, decoder = lz.split(marker, 1)
if "int hd11_uncompress_bounded(" in lz:
    raise SystemExit("STOP: Bounded load already staged")
declaration = re.compile(r'(\bint\s+code_count\s*=\s*TABSIZE\s*-\s*256\s*;)')
decoder, n = declaration.subn(r'\1\n    int hd11_depth;',decoder,count=1)
if n != 1:
    raise SystemExit("STOP: Decoder variable anchor not matched")
decoder, n = re.subn(r'\bcode\s*=\s*oldcode\s*=\s*getcode\(\s*\)\s*;',
    "code = oldcode = getcode();\n"
    "    if (code == UEOF || code >= TABSIZE || !string_tab[code].used)\n"
    "        return(-1);", decoder,count=1)
if n != 1:
    raise SystemExit("STOP: First LZW code anchor not matched")
decoder, n = re.subn(r'\bwhile\s*\(\s*ep->predecessor\s*!=\s*NO_PRED\s*\)\s*\{',
    "hd11_depth = 0;\n"
    "        while(ep->predecessor != NO_PRED) {\n"
    "            if (++hd11_depth > TABSIZE || !ep->used ||\n"
    "                ep->predecessor >= TABSIZE)\n"
    "                return(-1);",decoder,count=1)
if n != 1:
    raise SystemExit("STOP: LZW dictionary walk anchor not matched")

# The original push stack check occurs *after* writing. Bound before writing
# and mark the existing wrapper error flag for the new bounded decoder.
push_marker="void push(c)"
if decoder.count(push_marker) != 1:
    raise SystemExit("STOP: Native push function anchor not unique")
head, tail = decoder.split(push_marker,1)
match = re.search(
    r'stack\s*\[\s*sp\s*\]\s*=\s*\(char\)\s*c\s*;\s*'
    r'sp\+\+;\s*'
    r'if\s*\(\s*sp\s*>=\s*STACKSIZE\s*\)\s*'
    r'merror\s*\([^;]*\);',tail)
if match is None:
    raise SystemExit("STOP: Original stack check does not match")
tail = tail[:match.start()] + (
    "if (sp >= STACKSIZE) {\n"
    "        hd11_lzw_overflow = 1;\n"
    "        return;\n"
    "    }\n"
    "    stack[sp++] = (char)c;") + tail[match.end():]
decoder = head+push_marker+tail

# Defined only for COMPRESS builds, and statically reusable from files2.c.
wrapper = r"""
/* Private Round11F: bounded decoder, same native LZW file format. */
int hd11_uncompress_bounded(char *input, char *output,
                            int compressed_size, int output_cap)
{
    int decoded;
    if (!input || !output || compressed_size < 2 ||
        compressed_size >= 50000 || output_cap < 1 ||
        output_cap > 99999 || hd11_lzw_cap != 0)
        return(-1);
    hd11_lzw_overflow = 0;
    hd11_lzw_cap = output_cap;
    decoded = uncompress(input, output, compressed_size);
    hd11_lzw_cap = 0;
    if (hd11_lzw_overflow || decoded < 1 || decoded > output_cap)
        return(-1);
    return(decoded);
}

"""
lz = before + wrapper + marker + decoder

begin = files.index("int load_ply(str, ply_ptr)")
tail = files[begin:]
boundary = re.search(r'\n/\*{16,}/', tail)
if boundary is None:
    raise SystemExit("STOP: Native loader boundary absent")
end = begin+boundary.start()
old_load = files[begin:end]
if "return(0);" not in old_load or "int save_ply(" in old_load:
    raise SystemExit("STOP: Native loader body unexpected")

bounded_load = r"""/*
 * Private Round11F bounded player format preflight.
 * Use native creature/object layout, reject invalid nested counts,
 * overlong recursion, malformed raw length, or mismatched account name
 * BEFORE entering the legacy allocating read_crt_from_mem function.
 */
extern int hd11_uncompress_bounded(char *, char *, int, int);

static int hd11_raw_object(const char *buf, size_t length,
                           size_t *offset, unsigned int depth,
                           unsigned int *total)
{
    int count, i;
    if (depth > HD11_MAX_DEPTH || *total >= HD11_ITEM_MAX ||
        *offset > length ||
        length - *offset < sizeof(object) + sizeof(int))
        return(-1);
    ++(*total);
    *offset += sizeof(object);
    memcpy(&count, buf + *offset, sizeof(int));
    *offset += sizeof(int);
    if (count < 0 || (unsigned int)count > HD11_ITEM_MAX)
        return(-1);
    for (i = 0; i < count; i++) {
        if (hd11_raw_object(buf,length,offset,depth+1,total) < 0)
            return(-1);
    }
    return(0);
}

static int hd11_raw_player_valid(const char *buf, size_t length,
                                 const char *expected_name)
{
    int count, i;
    size_t offset = 0;
    unsigned int total = 0;
    char saved_name[sizeof(((creature *)0)->name) + 1];
    if (!buf || !hd11_name_valid(expected_name) ||
        length < sizeof(creature)+sizeof(int) ||
        length > HD11_SAVE_RAW_LIMIT)
        return(0);
    memcpy(saved_name,buf,sizeof(((creature *)0)->name));
    saved_name[sizeof(((creature *)0)->name)] = 0;
    if (!memchr(saved_name,0,sizeof(((creature *)0)->name)) ||
        strcmp(saved_name,expected_name))
        return(0);
    offset = sizeof(creature);
    memcpy(&count,buf+offset,sizeof(int));
    offset += sizeof(int);
    if (count < 0 || (unsigned int)count > HD11_ITEM_MAX)
        return(0);
    for (i = 0; i < count; i++) {
        if (hd11_raw_object(buf,length,&offset,1,&total) < 0)
            return(0);
    }
    return(offset == length);
}

/* Return -1 only for missing name; -2 for corrupt/unsafe existing files.
 * Native login must explicitly reject a preexisting unreadable character.
 */
int load_ply(str, ply_ptr)
char *str;
creature **ply_ptr;
{
#ifdef COMPRESS
    char path[256], *packed = 0, *raw = 0;
    struct stat st, opened;
    int fd = -1, outcome = -2;
    int raw_size, consumed;
    size_t have = 0, wanted;
    ssize_t n;
    creature *loaded = 0;

    if (!ply_ptr) return(-2);
    *ply_ptr = 0;
    if (!hd11_name_valid(str) ||
        snprintf(path, sizeof(path), "%s/%s", PLAYERPATH,str) < 0 ||
        strlen(PLAYERPATH)+strlen(str)+2 >= sizeof(path))
        return(-2);
    if (lstat(path,&st) < 0)
        return(errno == ENOENT ? -1 : -2);
    if (!S_ISREG(st.st_mode) || st.st_nlink != 1 ||
        st.st_uid != geteuid() ||
        st.st_size < 2 || st.st_size >= 50000)
        return(-2);
    fd = open(path,O_RDONLY | O_BINARY | O_NOFOLLOW);
    if (fd < 0) return(-2);
    if (fstat(fd,&opened) < 0 ||
        opened.st_dev != st.st_dev || opened.st_ino != st.st_ino ||
        opened.st_size != st.st_size ||
        !S_ISREG(opened.st_mode)) goto done;
    wanted = (size_t)opened.st_size;
    packed = (char *)malloc(wanted);
    raw = (char *)malloc(HD11_SAVE_RAW_LIMIT);
    if (!packed || !raw) goto done;
    while (have < wanted) {
        n = read(fd, packed+have, wanted-have);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) goto done;
        have += (size_t)n;
    }
    if (close(fd) < 0) { fd=-1; goto done; }
    fd=-1;
    raw_size = hd11_uncompress_bounded(packed, raw, (int)wanted,
                                       HD11_SAVE_RAW_LIMIT);
    if (raw_size <= 0 ||
        !hd11_raw_player_valid(raw,(size_t)raw_size,str))
        goto done;
    loaded = (creature *)malloc(sizeof(creature));
    if (!loaded) goto done;
    consumed = read_crt_from_mem(raw,loaded,0);
    if (consumed != raw_size) goto done;
    *ply_ptr = loaded;
    loaded = 0;
    outcome = 0;
done:
    if (loaded) free_crt(loaded);
    if (packed) free(packed);
    if (raw) free(raw);
    if (fd >= 0) close(fd);
    return(outcome);
#else
    return(-2);
#endif
}
"""
files = files[:begin] + bounded_load + files[end:]

# Existing corrupt character must NEVER be offered new account creation.
login_re = re.compile(
    r'\bif\s*\(\s*load_ply\s*\(\s*str\s*,\s*&ply_ptr\s*\)\s*<\s*0\s*\)\s*\{')
matched = list(login_re.finditer(login))
if len(matched) != 1:
    raise SystemExit("STOP: Found {} native login account checks (expected 1)".format(len(matched)))
guard = r"""if(load_ply(str, &ply_ptr) < 0) {
            /* Round11F: a corrupt existing save is NOT a new character. */
            char hd11_existing_character_unreadable[256];
            struct stat hd11_existing_stat;
            int hd11_path_len = snprintf(
                hd11_existing_character_unreadable,
                sizeof(hd11_existing_character_unreadable),
                "%s/%s",PLAYERPATH,str);
            if (hd11_path_len < 0 ||
                hd11_path_len >= (int)sizeof(hd11_existing_character_unreadable) ||
                lstat(hd11_existing_character_unreadable,
                      &hd11_existing_stat) == 0 ||
                errno != ENOENT) {
                print(fd,"Existing character data cannot be loaded. Contact staff.\n");
                disconnect(fd);
                return;
            }
"""
login = login_re.sub(lambda m:guard,login,count=1)
anchor = '#include "mextern.h"'
if login.count(anchor) != 1:
    raise SystemExit("STOP: Login source includes unexpected")
login = login.replace(anchor,anchor +
    '\n#include <errno.h>\n#include <sys/stat.h>\n#include <stdio.h>',1)

updates = [
    (path_lzw, lz),
    (path_files, files),
    (path_login, login),
]
for path, value in updates:
    backup=path.with_name(path.name+".before-round11f")
    if backup.exists() or backup.is_symlink():
        raise SystemExit("STOP: Private backup exists: "+str(backup))
for path, value in updates:
    backup=path.with_name(path.name+".before-round11f")
    backup.write_text(path.read_text())
    backup.chmod(0o600)
    path.write_text(value)

assert files.count("int load_ply(str, ply_ptr)") == 1
assert "hd11_uncompress_bounded" in lz
assert "hd11_raw_player_valid" in files
assert "hd11_existing_character_unreadable" in login
print("Private LZW: BOUNDED DECODER + STACK/DICTIONARY GUARDS")
print("Private files2.c: NATIVE-FORMAT LENGTH/OBJECT VALIDATOR + SAFE LOAD")
print("Private command1.c: PREEXISTING CORRUPT ACCOUNT CREATION DENIED")
print("Original 11D atomic native saver: PRESERVED")
print("Prior Round11D engine, players and guild ledger: UNMODIFIED")
print("Original production source, rooms and website: NOT TOUCHED")
