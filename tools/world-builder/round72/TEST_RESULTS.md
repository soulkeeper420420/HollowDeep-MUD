# Round 72 · Linode validation

Executed in a disposable checkout from `974f03be35ae9901c82b034ff5d0a2326a21718b` on 2026-11-15.

| Check | Observed result |
| --- | --- |
| Isolated engine compilation | 32-bit ELF built from a fresh copy of the Round 71 private source |
| Terrain and plan validation | Same-seed plans matched. Different seeds produced different map data. All seven terrains appeared. All 100 rooms through ID 15999 were reachable. Restrictions, reserved ranges, invalid seeds, duplicate coordinates and mismatched exits were checked. |
| Chromium/Playwright | Rounds 60–72 builder checks passed, including named drafts, import/export, recovery, undo, navigation guards, connection audit, custom entities, seeded terrain, map preview, landmark edits and the new ZIP download. |
| Native wilderness | Installed the browser-produced ZIP in a fresh test world. The map rendered coordinates, the landmark, unknown terrain and ANSI road color. It updated when the player moved east and west and returned to the old world. |
| Legacy native gameplay | Round 59–71 replay passed. It covered existing room records and carried inventory, navigation, placed and custom monsters and objects, defeat, respawn, pickup and removed placements. |
| Native equipment | A separate replay used an ABI-checked test copy of Practice Blade with a command keyword and wield slot. Pickup, wielding and the equipment list passed. |
| Production integrity | Source, rooms, object/monster trees, running executable, service identity, prior private engine source and fixture matched before and after. The service remained active. |

The consolidated harness exited successfully with 125 `PASS:` lines in the replay log and 29 in the builder regression log, in addition to the round-level pass markers.

- Isolated ELF SHA-256: `4c768ece3cd882631d874d9920946ceafe6bc6e4c3166fa7bec1cba351bc291c`
- Browser wilderness ZIP SHA-256: `10a2fdc782878f2f9697383449bce9b73d64890d031b822ade94ee21ab1bf2aa`

## Wilderness draft transfer follow-up

A focused Linode replay exported the named Copperreach draft, imported it in a fresh Chromium context, and verified exact plan equality, including terrain, coordinates, landmark and exits. It rejected a zero column without changing the imported plan. The native game loaded the ZIP exported from the imported draft and passed map, ANSI, and travel checks.

- Re-imported draft ZIP SHA-256: `a0c9e5f026ef4a05d07d629128cc6a1abd6e519a3bbb9b55c4f1e6b71b704c30`
