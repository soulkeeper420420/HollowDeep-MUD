#!/usr/bin/env python3
"""Guarded Round 11D save-only candidate, created in a fresh private source copy.

Stage only: replace native save_ply with bounded recursive native-format
serialization, bounded LZW output, and same-directory fsync/rename commit.
The original native load_ply is untouched pending separate bounded-load work.
"""
from pathlib import Path
import re
import sys

ROOT = Path("/root/hollowdeep-dev/guild-social-batch1")
if len(sys.argv) != 2:
    raise SystemExit("STOP: Provide the new private source directory")
src = Path(sys.argv[1]).resolve(strict=True)
if (src.parent.parent != ROOT or
        not src.parent.name.startswith("round11-atomic-") or
        src.name != "src"):
    raise SystemExit("STOP: Not a fresh private Round11D source")
for name in ("files2.c", "compress.c", "Makefile"):
    f = src / name
    if not f.is_file() or f.is_symlink():
        raise SystemExit("STOP: Required private source missing/symlinked: " + name)

files2 = (src / "files2.c").read_text()
lz = (src / "compress.c").read_text()

if "HD11_SAVE_RAW_LIMIT" in files2 or "hd11_compress_bounded" in lz:
    raise SystemExit("STOP: Already patched, refuse double application")
if not re.search(r'int\s+save_ply\(str,\s*ply_ptr\)\s*char\s*\*\s*str\s*;\s*creature\s*\*\s*ply_ptr\s*;', files2):
    raise SystemExit("STOP: Native K&R two-argument save signature changed")
for anchor in ('rename(file, filebak);', 'write_crt_to_mem(a_buf, ply_ptr, 0);',
               'size = compress(a_buf, b_buf, n);', 'unlink(filebak);'):
    if anchor not in files2:
        raise SystemExit("STOP: Unexpected original native save: " + anchor)
if lz.count("unsigned int writec(ch)") != 1 or lz.count("void flushout()") != 1:
    raise SystemExit("STOP: Unknown LZW writer implementation")
if "int compress(in, out, size)" not in lz or "int uncompress(in, out, size)" not in lz:
    raise SystemExit("STOP: Unknown LZW entry points")

# Patch only the global LZW output writer and add a bounded compression API.
anchor = re.search(r'(static\s+int\s+sizeof_inbuf\s*,\s*sizeof_outbuf\s*;)', lz)
if not anchor:
    raise SystemExit("STOP: LZW output byte counter not found")
lz = lz[:anchor.end()] + """

/* Round 11D: temporary capacity used only by hd11_compress_bounded. */
static int hd11_lzw_cap = 0;
static int hd11_lzw_overflow = 0;
""" + lz[anchor.end():]

write_begin = lz.index("unsigned int writec(ch)")
write_end = lz.index("int compress(in, out, size)", write_begin)
assert "void flushout()" in lz[write_begin:write_end]
lz = lz[:write_begin] + """unsigned int writec(ch)
int ch;
{
    if (hd11_lzw_cap > 0 && sizeof_outbuf >= hd11_lzw_cap) {
        hd11_lzw_overflow = 1;
        return(0);
    }
    *outbuf++ = (char)ch;
    sizeof_outbuf++;
    return(0);
}

void flushout()
{
    if (temp_outbuf != EMPTY) {
        if (hd11_lzw_cap > 0 && sizeof_outbuf >= hd11_lzw_cap) {
            hd11_lzw_overflow = 1;
            return;
        }
        *outbuf++ = (char)((temp_outbuf << 4) & 0xFF0);
        sizeof_outbuf++;
    }
}

""" + lz[write_end:]

uncomp = "int uncompress(in, out, size)"
if lz.count(uncomp) != 1:
    raise SystemExit("STOP: LZW insertion point not unique")
lz = lz.replace(uncomp, """/*
 * Bounds-check the existing 12-bit LZW writer without changing the
 * native compressed file format or the original uncompress entrypoint.
 * Single-threaded engine: the pre-existing compressor already uses globals.
 */
int hd11_compress_bounded(char *input, char *output, int input_len, int output_cap)
{
    int written;
    if (!input || !output || input_len < 1 || output_cap < 1)
        return(-1);
    if (hd11_lzw_cap != 0)
        return(-1);
    hd11_lzw_cap = output_cap;
    hd11_lzw_overflow = 0;
    written = compress(input, output, input_len);
    hd11_lzw_cap = 0;
    if (hd11_lzw_overflow || written < 1 || written > output_cap)
        return(-1);
    return(written);
}

""" + uncomp, 1)

include = '#include "mextern.h"'
if files2.count(include) != 1:
    raise SystemExit("STOP: files2 include anchor mismatch")
files2 = files2.replace(include, include + """
#include <errno.h>
#include <ctype.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
""", 1)

start = files2.index("int save_ply(str, ply_ptr)")
banner = re.search(r'\n/\*{16,}/', files2[start:])
if not banner:
    raise SystemExit("STOP: Could not locate load_ply comment after save_ply")
end = start + banner.start()
original = files2[start:end]
if "int load_ply(" in original or "return(0);" not in original:
    raise SystemExit("STOP: Unexpected save function boundary")

candidate = r"""/*
 * Round 11D, PRIVATE TEST ONLY: native-format bounded save.
 * Do not promote without bounded deserializer, fault injection, and review.
 *
 * Raw format remains: creature struct, direct item count, recursively
 * object struct and direct contained-object count (all native sizes).
 * HD11_ITEM_MAX is an intentionally conservative fail-closed budget.
 */
#define HD11_SAVE_RAW_LIMIT 99999U
#define HD11_SAVE_COMP_LIMIT 49999
#define HD11_ITEM_MAX 512U
#define HD11_MAX_DEPTH 24U

extern int hd11_compress_bounded(char *, char *, int, int);

static int hd11_put_bytes(char *buf, size_t cap, size_t *used,
                         const void *bytes, size_t amount)
{
    if (!buf || !used || !bytes || *used > cap ||
        amount > cap - *used)
        return(-1);
    memcpy(buf + *used, bytes, amount);
    *used += amount;
    return(0);
}

static int hd11_put_object(char *buf, size_t cap, size_t *used,
                           object *item, unsigned int depth,
                           unsigned int *total)
{
    otag *tag;
    int count, seen = 0;
    if (!item || !total || depth > HD11_MAX_DEPTH ||
        *total >= HD11_ITEM_MAX)
        return(-1);
    (*total)++;
    count = count_obj(item, 0);
    if (count < 0 || (unsigned int)count > HD11_ITEM_MAX ||
        hd11_put_bytes(buf, cap, used, item, sizeof(object)) < 0 ||
        hd11_put_bytes(buf, cap, used, &count, sizeof(int)) < 0)
        return(-1);
    for (tag = item->first_obj; tag; tag = tag->next_tag) {
        if (seen >= count || !tag->obj ||
            hd11_put_object(buf, cap, used, tag->obj,
                            depth + 1, total) < 0)
            return(-1);
        seen++;
    }
    return(seen == count ? 0 : -1);
}

static int hd11_put_player(char *buf, size_t cap, creature *player)
{
    otag *tag;
    size_t used = 0;
    unsigned int total = 0;
    int count, seen = 0;
    if (!buf || !player || cap > HD11_SAVE_RAW_LIMIT)
        return(-1);
    count = count_inv(player, 0);
    if (count < 0 || (unsigned int)count > HD11_ITEM_MAX ||
        hd11_put_bytes(buf, cap, &used, player, sizeof(creature)) < 0 ||
        hd11_put_bytes(buf, cap, &used, &count, sizeof(int)) < 0)
        return(-1);
    for (tag = player->first_obj; tag; tag = tag->next_tag) {
        if (seen >= count || !tag->obj ||
            hd11_put_object(buf, cap, &used, tag->obj, 1, &total) < 0)
            return(-1);
        seen++;
    }
    if (seen != count || used == 0 || used > HD11_SAVE_RAW_LIMIT)
        return(-1);
    return((int)used);
}

static int hd11_name_valid(const char *name)
{
    size_t i, n;
    if (!name) return(0);
    n = strlen(name);
    if (n < 3 || n >= 20) return(0);
    for (i = 0; i < n; i++) {
        unsigned char c = (unsigned char)name[i];
        if (!((c >= 'a' && c <= 'z') ||
              (c >= 'A' && c <= 'Z')))
            return(0);
    }
    return(1);
}

static int hd11_atomic_player_write(const char *name,
                                     const char *payload, size_t size)
{
    char file[256], temporary[256];
    struct stat st;
    int fd = -1, directory_fd = -1, installed = 0, result = -1;
    size_t written = 0;
    ssize_t n;
    if (!hd11_name_valid(name) || !payload || size == 0 ||
        size >= 50000U ||
        snprintf(file, sizeof(file), "%s/%s", PLAYERPATH, name) < 0 ||
        strlen(PLAYERPATH) + strlen(name) + 2 >= sizeof(file) ||
        snprintf(temporary, sizeof(temporary),
                 "%s/.hd11-%s-XXXXXX", PLAYERPATH, name) < 0 ||
        strlen(PLAYERPATH) + strlen(name) + 15 >= sizeof(temporary))
        return(-1);

    if (lstat(PLAYERPATH, &st) < 0 ||
        !S_ISDIR(st.st_mode) || st.st_uid != geteuid())
        return(-1);
    if (lstat(file, &st) == 0) {
        if (!S_ISREG(st.st_mode) || st.st_nlink != 1 ||
            st.st_uid != geteuid())
            return(-1);
    } else if (errno != ENOENT)
        return(-1);

    fd = mkstemp(temporary);
    if (fd < 0) return(-1);
    if (fchmod(fd, 0660) < 0) goto done;
    while (written < size) {
        n = write(fd, payload + written, size - written);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) goto done;
        written += (size_t)n;
    }
    if (fsync(fd) < 0) goto done;
    if (close(fd) < 0) {
        fd = -1;
        goto done;
    }
    fd = -1;
    if (rename(temporary, file) < 0) goto done;
    installed = 1;
    directory_fd = open(PLAYERPATH, O_RDONLY);
    if (directory_fd < 0 || fsync(directory_fd) < 0)
        goto done;
    result = 0;

done:
    if (fd >= 0) close(fd);
    if (directory_fd >= 0) close(directory_fd);
    if (!installed) unlink(temporary);
    return(result);
}

/*
 * Retain the native K&R signature and load_ply-compatible file format.
 * Unlike the old routine, keep the previous primary untouched until a
 * complete candidate has been written and synchronized.
 */
int save_ply(str, ply_ptr)
char *str;
creature *ply_ptr;
{
#ifdef COMPRESS
    char *raw = 0, *packed = 0;
    int raw_size, packed_size, status = -1;
    if (!str || !ply_ptr || strcmp(str, ply_ptr->name))
        return(-1);
    raw = (char *)malloc(HD11_SAVE_RAW_LIMIT);
    packed = (char *)malloc(HD11_SAVE_COMP_LIMIT);
    if (!raw || !packed) goto done;
    raw_size = hd11_put_player(raw, HD11_SAVE_RAW_LIMIT, ply_ptr);
    if (raw_size <= 0) goto done;
    packed_size = hd11_compress_bounded(
        raw, packed, raw_size, HD11_SAVE_COMP_LIMIT);
    if (packed_size <= 0 || packed_size >= 50000) goto done;
    status = hd11_atomic_player_write(str, packed, (size_t)packed_size);
done:
    if (raw) free(raw);
    if (packed) free(packed);
    return(status);
#else
    /* This candidate is deliberately scoped to the COMPRESS-enabled MUD. */
    return(-1);
#endif
}

"""
files2 = files2[:start] + candidate + files2[end:]

for fname, before, after in (
    ("files2.c", (src / "files2.c").read_text(), files2),
    ("compress.c", (src / "compress.c").read_text(), lz),
):
    path = src / fname
    backup = src / (fname + ".before-round11d")
    if backup.exists() or backup.is_symlink():
        raise SystemExit("STOP: Existing private backup; no overwrite: " + str(backup))
    backup.write_text(before)
    backup.chmod(0o600)
    path.write_text(after)

if "save_ply(str, ply_ptr)" not in files2 or "hd11_put_object" not in files2:
    raise SystemExit("STOP: Candidate postcondition failed")
if "int hd11_compress_bounded" not in lz:
    raise SystemExit("STOP: LZW postcondition failed")
print("Private files2.c: BOUNDED NATIVE-FORMAT WRITER + ATOMIC SAVE CANDIDATE")
print("Private compress.c: BOUNDED LZW OUTPUT API")
print("Original native load_ply: UNCHANGED (still needs hardening)")
print("Previous Round 10 tested binaries/player files: UNTOUCHED")
print("Production engine, rooms, players and website: NOT MODIFIED")
