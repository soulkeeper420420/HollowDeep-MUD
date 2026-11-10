# HollowDeep Guild & Social V2 — Experimental Charter and Housing

**Staging only. Do not deploy to the live game.** The C code is a new experimental implementation derived from HollowDeep's original social module, not Atlas MUD code. It keeps existing staff roles and builder restrictions separate.

## Features implemented in source (not yet compiled or playtested)

- A native **2,500-gold Clan Deed** purchased through the existing `RSHOPP` merchant in room 6000 (stockroom 6001). A targeted patch to copied `command7.c` mints an unpredictable **128-bit serial** in the cloned deed's `use_output`, without changing the inventory template or generic purchases.
- `clan create <name>` requires a matching, unused minted physical deed. One atomic registry file commit (`HDGUILD2`) records the new guild, founding leader, assigned hall, and the **spent unique serial**. On failed registry write the item is not consumed. After success the code removes the physical item and asks native `save_ply` to save immediately.
- Crash between registry commit and native character save can leave an already-spent item in the character file; a spent serial can never found another guild, and the next `clan` command reconciles it. **Native character-save failure detection and filesystem crash fault injection are not yet verified.**
- Three starter guild halls are assigned in order: 6003, 6006, 6009. Hall membership checks are enforced in the private copies of standard `go`, `sneak`, and centrally in `add_ply_rom` (to cover login, teleport, traps and other routes). Unauthorized hall entry falls back to the public square. Staff bypass consults the existing **HollowDeep role database**, not character class alone.
- V2 test-world generator makes a connected public square and three hall entrances, but its output path is restricted to disposable `round10-*/test-world/rooms`. Nothing touches the production world.
- `round10_runner.py` automates physical purchase, two guild founders, one invited member, access denials, permitted movement, save/restart and spent-serial durability. The prior Round 9 `r9fund` command is carried forward only in a private test executable.

## Compatibility / safety

The registry can read legacy `HDGUILD1` records (without hall IDs) and writes `HDGUILD2`. Migration, collision behavior, backup/rollback and tamper/corruption recovery must be tested. The 256-entry redemption capacity and three fixed halls are intentional **prototype** limits, not a final service architecture. No deed-free bypass exists in this V2 implementation.

**No user result yet for Round 10.** The successful prior Round 9B native shop playtest verified 21/21 purchase and restart checks, but not the V2 redemption or ACL changes.

Do not publish the test-gold helper into any production source or run any copied test executable outside a disposable chroot and private network namespace. Do not claim the public PHP website provides game guild functionality.
