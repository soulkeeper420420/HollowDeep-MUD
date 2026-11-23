# HollowDeep MUD — Round79AC3A private native lifecycle map

This is a **read-only** native-source audit, not mount gameplay. Accepted source baseline: Round79AC2 R2 (full ELF32 and socket tests passed). In private Linode source `/tmp/hd-army-game-round79worldproof-*/src`, locate actual creature insertion, removal, free, and player logout callsites. Unlike a name-based mount or a receipt-only location claim, native owned mount authority requires *trusted* monster spawn and revocation whenever a creature leaves the world, is destroyed, is reused, or its owner disconnects.

The runner inventories concrete C source locations and rejects unexpected invocations of the new binding API outside its implementation. Until those callsites are reviewed and instrumented, no authority may be created by player commands; boarding, stabling, retrieval, and ridden wilderness remain disabled. Existing native structures, gameplay, saves, service, world, and player files are not modified.

The audit tests contain only synthetic temporary C source; logs remain on Linode and do not belong in GitHub. A passing audit proves scan integrity and absence of premature hooks; it **does not** establish that all death/logout/unload paths have been hooked. Subsequent AC3B will bind tokens only from trusted native creature creation and revoke on all relevant removal paths with isolated gameplay tests.

Run `private_lifecycle_audit_round79ac3a.sh WORK SOURCE` from the pinned test candidate checkout, with a fresh `/root/hollowdeep-dev/round79ac3a-*` work directory and accepted Round79AC2 R2 private `/tmp/hd-army-game-round79worldproof-*/src` source.

Accepted on Linode: audit exit code 0, private native source inventory PASS, production PID/binary and accepted ELF32 baseline unchanged. Report: 19 del_crt_rom references, 24 free_crt references, 20 del_ply_rom references, and no native mount identity hook callsites outside their own implementation. Private results: `/root/hollowdeep-dev/round79ac3a-o8Xx5d59` (not published). This inventory is NOT proof that all delete paths are hooked; it is the basis for AC3B's mandatory central-hook validation.

Tests: eight synthetic Python auditor tests and the read-only Linode source inventory PASS. Production deployment: none.
