#!/usr/bin/env python3
"""Guarded Round 10 staging fix for native save_ply and chroot randomness.

Only repairs the two nonexistent PSAVES flag wrappers and replaces
/dev/urandom-dependent deed minting with the Linux getrandom syscall.
The live MUD tree is never read or written by this helper.
"""
from pathlib import Path
import os, sys, tempfile

ROOT = Path("/root/hollowdeep-dev/guild-social-batch1/round10-PpNpn17k/src")
if len(sys.argv) != 2 or Path(sys.argv[1]).resolve() != ROOT:
    raise SystemExit("STOP: Refusing any path outside the exact private Round 10 workspace")
p = ROOT / "hollowdeep_social.c"
if not p.is_file() or p.is_symlink():
    raise SystemExit("STOP: Missing or symlinked staged social source")
s = p.read_text()
old_a = """        F_SET(player, PSAVES);
        save_ply(player);
        F_CLR(player, PSAVES);"""
old_b = """                F_SET(player, PSAVES);
                save_ply(player);
                F_CLR(player, PSAVES);"""
old_header = "#include <sys/stat.h>\n#include <time.h>"
old_crypto = """    fd = open("/dev/urandom", O_RDONLY | O_NOFOLLOW);
    if (fd < 0) return 0;
    i = (int)read(fd, bytes, sizeof(bytes));
    close(fd);
    if (i != (int)sizeof(bytes)) return 0;"""
old_decl = """int hd_guild_mint_deed(object *item)
{
    int fd, i;
    unsigned char bytes[16];"""

expected = [(old_a, 1), (old_b, 1), (old_header, 1),
            (old_crypto, 1), (old_decl, 1)]
for text, count in expected:
    found = s.count(text)
    if found != count:
        raise SystemExit("STOP: Unexpected staged native save / deed code, expected " +
                         str(count) + " match, got " + str(found) + ": " + text[:65])

s = s.replace(old_a, """        /* HollowDeep saves native character data directly. */
        save_ply(player);""", 1)
s = s.replace(old_b, """                /* HollowDeep saves native character data directly. */
                save_ply(player);""", 1)
s = s.replace(old_header,
              "#include <sys/stat.h>\n#include <sys/syscall.h>\n#include <time.h>", 1)
s = s.replace(old_decl, old_decl.replace("int fd, i;", "int i;"), 1)
s = s.replace(old_crypto, """    /* Linux kernel randomness also works in our disposable chroot. */
    if (syscall(SYS_getrandom, bytes, sizeof(bytes), 0) != (long)sizeof(bytes))
        return 0;""", 1)

if "PSAVES" in s or 'open("/dev/urandom"' in s:
    raise SystemExit("STOP: Unsupported staging save flag / random dependency remains")

# Keep one private source backup. Do not overwrite a previous one.
backup = ROOT / "hollowdeep_social.c.before-round10-save-fix"
if backup.exists() or backup.is_symlink():
    raise SystemExit("STOP: Private source backup already exists; abort to avoid overwrite")
with backup.open("x") as out:
    out.write_text(p.read_text())
os.chmod(backup, 0o600)
fd, temp_name = tempfile.mkstemp(prefix=".round10-social-", dir=ROOT)
try:
    with os.fdopen(fd, "w") as out:
        out.write(s)
        out.flush()
        os.fsync(out.fileno())
    os.chmod(temp_name, p.stat().st_mode & 0o777)
    os.replace(temp_name, p)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

print("Native save_ply calls: PRESERVED")
print("Unsupported PSAVES flags: REMOVED (2 call sites)")
print("Deed random serials: Linux getrandom syscall (no /dev required)")
print("Only private staged social source: UPDATED")
print("Production source: NOT TOUCHED")
