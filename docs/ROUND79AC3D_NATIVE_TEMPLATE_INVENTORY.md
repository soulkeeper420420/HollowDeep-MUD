# Round79AC3D — Native monster-template inventory (private candidate)

The accepted AC3C spawn backend has **no approved template IDs**. This audit determines which native monster records might be relevant without claiming that names or appearance establish authorization.

The private runner compiles a 32-bit ABI probe against the accepted native source and checks the known 1,184-byte ELF32 `creature` layout. It reads only native monster template files `m00` through `m29` (100 records per file), following the original `load_crt_from_file` convention. It discovers a single monster database under `/srv/hollowdeep/world`, excludes player directories, bounds all reads, checks actual native monster type, name, level and HP, then prints a limited candidate shortlist.

This is **READ-ONLY**. No live binary, service, world, player save or mount state is changed. Candidate names and IDs remain in the private Linode log; never commit them or post private fixtures/records on Discord. Nothing enables spawning, boarding, stabling, retrieval, reconnect, or mounted travel. A later approval/validation stage must verify each candidate's actual stats, abilities, loot, attack/death/respawn behavior and model compatibility before authorizing any mapping.

Run `private_native_template_inventory_round79ac3d.sh WORK SOURCE` from the pinned private candidate, with `SOURCE=/tmp/hd-army-game-round79trustedspawn-3W2RXVIA/src`. The runner refuses ambiguous or incompatible monster databases. Nine synthetic scanner tests are included; Linode ELF32 and real template verification remain pending. Production deployment: none.

## R2 native source layout fix (unaccepted)

The first Linode runner stopped at a hardcoded `$SOURCE/files4.c` check: the private native ELF32 source does not include that translation unit, even though the built executable includes the native monster loader. No binary was compiled or world scanned in that run. The original Mordor loader's `mNN` convention is retained, but R2 attempted to verify `MFILESIZE=100` and incorrectly hardcoded `CMAX=3000` in the ELF32 ABI probe alongside the `creature` size/offsets. The source-filename assumption is removed. Changed constants, missing ABI metadata, or a missing/ambiguous monster database fail closed.

The R2 local/ELF32 native audit has not yet been confirmed on Linode. No production modifications.

## R3 actual HollowDeep CMAX audit repair (pending Linode validation)

The R2 private ELF32 probe compiled and ran successfully, returning `HD79_NATIVE_ABI 1184 0 319 318 332 334 1 100 1000`. This confirms `CMAX=1000` for the tested native build, rather than the upstream Mordor `3000`. R2 refused the mismatch before reading any monster records. R3 carries the real compiled `CMAX` through ABI validation and the template file scan: this build may read only `m00`–`m09` (1,000 index slots) and cannot inspect `m10` or higher. The scanner retains a conservative maximum of 3,000 and rejects missing, non-divisible, out-of-range or untrusted limits. New regressions test the real 1,000-slot ABI, boundary file indexing, 3,000-slot compatibility, and invalid limits.

The actual monster template audit on Linode is **still pending**. No template IDs are approved, no trusted catalog is configured, and no world/game/player files have been edited.
