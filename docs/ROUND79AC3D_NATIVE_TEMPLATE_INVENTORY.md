# Round79AC3D — Native monster-template inventory (private candidate)

The accepted AC3C spawn backend has **no approved template IDs**. This audit determines which native monster records might be relevant without claiming that names or appearance establish authorization.

The private runner compiles a 32-bit ABI probe against the accepted native source and checks the known 1,184-byte ELF32 `creature` layout. It reads only native monster template files `m00` through `m29` (100 records per file), following the original `load_crt_from_file` convention. It discovers a single monster database under `/srv/hollowdeep/world`, excludes player directories, bounds all reads, checks actual native monster type, name, level and HP, then prints a limited candidate shortlist.

This is **READ-ONLY**. No live binary, service, world, player save or mount state is changed. Candidate names and IDs remain in the private Linode log; never commit them or post private fixtures/records on Discord. Nothing enables spawning, boarding, stabling, retrieval, reconnect, or mounted travel. A later approval/validation stage must verify each candidate's actual stats, abilities, loot, attack/death/respawn behavior and model compatibility before authorizing any mapping.

Run `private_native_template_inventory_round79ac3d.sh WORK SOURCE` from the pinned private candidate, with `SOURCE=/tmp/hd-army-game-round79trustedspawn-3W2RXVIA/src`. The runner refuses ambiguous or incompatible monster databases. Nine synthetic scanner tests are included; Linode ELF32 and real template verification remain pending. Production deployment: none.
