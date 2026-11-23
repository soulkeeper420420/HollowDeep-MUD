# HollowDeep Round79AC3E — Native mount-template risk review

Read-only private candidate. Round79AC3D R3 audited the real monster database and found 34 unapproved name matches. This candidate compiles an ELF32 native C offset probe and reads the same fixed-size mNN monster templates again to examine mana, attack dice, flag/spell/carry bytes and non-mount naming patterns.

All decisions are conservative: EXCLUDE_NAME, MANUAL_MAGIC_REVIEW or MANUAL_REVIEW. None can confer ownership, authorize a template, modify a trusted six-species catalog, trigger a spawn or enable board/stable/retrieve/reconnect/travel. Native template attributes and identifiers remain in private Linode output only.

Validation requires six synthetic tests, compiled native creature offset checks, comparison with the accepted read-only inventory and production PID/binary/ELF32 unchanged. The Linode run is pending. Do not commit private logs, fixtures, creature records, credentials or template IDs. No production deployment.

## AC3E R2 native array-size repair — private tests pending

The first Linode run completed six synthetic tests and both ELF32 probe compilations, then refused the real creature trait ABI. The original reviewer incorrectly assumed `flags=16`, `spells=16`, `carry=20` bytes, copied from the synthetic fixture rather than verified against this HollowDeep engine. The real probe output remains in the **private** `traits.log` of that run; its exact values were not included in the reported output, so no array sizes are guessed here.

R2 uses `sizeof(creature.flags/spells/carry)` from the private ELF32 probe as authoritative. Each is checked for a nonzero conservative byte bound, exact in-record offset and nonoverlap; carry must be an even number of bytes. Invalid or unfamiliar fields are still rejected. New regressions check variable sizes, zero/huge/odd arrays, overlap and out-of-record offsets. The private runner now prints only safe numeric offsets/sizes to make any next ABI failure directly diagnosable. The C probe does not inspect monster files. No trusted mount template is approved and no gameplay is enabled.

**Full native Linode validation pending. No production deployment.**
