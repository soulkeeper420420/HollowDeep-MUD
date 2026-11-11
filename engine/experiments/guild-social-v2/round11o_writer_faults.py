"""Exercise the real private atomic writer during the Round 11N replay."""
import runpy
import sys
from pathlib import Path

baseline = runpy.run_path(str(Path(__file__).with_name("round11n_patch.py")))
replace = baseline["replace"]
stage = Path(sys.argv[1])

# Move the failure from the caller to the writer's file-fsync boundary.
replace(stage / "src/hollowdeep_social.c",
        '''                if (unlink("/hollowdeep-data/round11n-character-fail") == 0 ||
                    hd_guild_save_equipped(player) < 0)''',
        "                if (hd_guild_save_equipped(player) < 0)")

files = stage / "src/files2.c"
replace(files, "    size_t written = 0;", """#ifndef HD_ROUND9_ISOLATED_FUNDS
#error "Round 11O faults require an isolated test build"
#endif
    int short_write = 0, fail_sync = 0;
    size_t written = 0;""")
replace(files, "    while (written < size) {", """    short_write = unlink("/hollowdeep-data/round11o-short-write") == 0;
    fail_sync = unlink("/hollowdeep-data/round11n-character-fail") == 0;
    while (written < size) {""")
replace(files, "        n = write(fd, payload + written, size - written);",
        """        n = write(fd, payload + written,
                  short_write && size - written > 7 ? 7 : size - written);""")
replace(files, "    if (fsync(fd) < 0) goto done;", """    if (fail_sync) {
        errno = EIO;
        goto done;
    }
    if (fsync(fd) < 0) goto done;""")

runner = stage / "runner.py"
replace(runner, '    created = command(a, "clan create Nightfall")',
        '''    short_marker = ledger_path.parent / "round11o-short-write"
    short_marker.touch()
    created = command(a, "clan create Nightfall")
    if short_marker.exists():
        raise RuntimeError("Native writer did not consume short-write fault")''')
replace(runner, '          stale_path.read_bytes() == stale_save)',
        '''          stale_path.read_bytes() == stale_save
          and not (ledger_path.parent / "round11n-character-fail").exists()
          and not list(stale_path.parent.glob(".hd11-*")))''')
